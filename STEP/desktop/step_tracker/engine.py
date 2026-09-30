"""Native capture worker, isolated from the UI and a single HTTPS network worker."""
import base64
import math
import queue
import random
import time
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from PySide6.QtCore import QThread, Signal

from .api import ApiClient, ApiError, backend_url
from .native import CapabilityError, Counters, active_app, mac_permissions, monitors, screenshot
from .storage import EncryptedStore, StorageError, Vault
from .sync import iso, reconcile, start_request, timestamp, utc_now


class Engine(QThread):
    changed = Signal(object)
    authenticated = Signal(object)
    monitor_list = Signal(object)
    preview = Signal(object)
    error = Signal(str)
    closed = Signal()

    def __init__(self):
        super().__init__()
        self.commands = queue.Queue()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="step-https")
        self.jobs = {}
        self.cancelled = threading.Event()
        self.store = self.api = self.vault = None
        self.user = self.config = None
        self.contracts = []
        self.screens = []
        self.mode = "Giriş bekleniyor"
        self.server_mode = None
        self.sync_message = ""
        self.selection = None
        self.current = None
        self.counters = None
        self.continuing = False
        self.idle_waiting = False
        self.idle_marker = None
        self.idle_resume_requested = False
        self.resume_activity = None
        self.quitting = False
        self.last_emit = self.last_sync = self.last_native = self.last_checkpoint = 0.0
        self.closed_flag = False

    def send(self, command, **values):
        self.commands.put((command, values))

    def _submit(self, kind, task, context=None):
        if kind in self.jobs:
            return False
        self.jobs[kind] = (self.pool.submit(task), context)
        return True

    def run(self):
        try:
            while not self.quitting:
                while True:
                    try:
                        command, values = self.commands.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        getattr(self, "_" + command)(**values)
                    except (CapabilityError, StorageError) as exc:
                        self._fail(str(exc))
                    except (ValueError, ApiError) as exc:
                        # Invalid owner decisions do not interrupt unrelated active work.
                        self.error.emit(str(exc))
                        if not self.current:
                            self.mode = str(exc)
                    except Exception:
                        self._fail("İşlem tamamlanamadı. Şifreli kayıtlar korundu; takip durduruldu.")
                self._poll_jobs()
                if self.current or self.idle_waiting:
                    try:
                        if self.current:
                            self._tick()
                        else:
                            self._idle_tick()
                    except (CapabilityError, StorageError, ValueError) as exc:
                        self._fail(str(exc))
                    except Exception:
                        self._fail("İşletim sistemi kaydı başarısız oldu. Takip durdu; kayıtlar şifreli kuyrukta.")
                now = time.monotonic()
                if self.store and now - self.last_sync >= 10 and not any(k in self.jobs for k in ("login", "start", "sync")):
                    self._sync()
                if now - self.last_emit >= 0.5:
                    try:
                        self._emit()
                    except StorageError as exc:
                        self._fail(str(exc))
                    self.last_emit = now
                time.sleep(0.1)
        finally:
            self._clear_idle()
            self.continuing = False
            if self.current:
                try:
                    self._finish(time.monotonic(), "Uygulama kapanıyor", False)
                except Exception:
                    pass  # The previous authenticated encrypted checkpoint remains available.
            if self.counters:
                self.counters.stop()
            # HTTPS requests have bounded timeouts; only this worker waits, never the UI.
            self.pool.shutdown(wait=True, cancel_futures=True)
            if self.store:
                self.store.close()
            self.closed_flag = True
            self.closed.emit()

    def _login(self, url, email, password, device_name, development=False, cached=False):
        if self.store or "login" in self.jobs:
            raise ValueError("Mevcut hesap kapanmadan hesap değiştirilemez.")
        base = backend_url(url, development)
        if not email.strip() or not device_name.strip():
            raise ValueError("E-posta ve cihaz adı gerekir.")
        def login():
            vault = Vault(base, email)
            api = ApiClient(base)
            store = EncryptedStore(vault)
            try:
                if cached:
                    token, expires = vault.get("device-token"), vault.get("device-expires")
                    if not token or not expires or timestamp(expires) <= utc_now():
                        raise ValueError("Kayıtlı cihaz oturumu yok veya süresi dolmuş. E-posta/şifre ile giriş yapın.")
                    api.token = token
                    user = store.get("meta", "user")
                    if not user:
                        raise ValueError("Bu hesabın güvenli cihaz kaydı bulunamadı.")
                else:
                    if not password:
                        raise ValueError("Şifre gerekir.")
                    result = api.request("POST", "auth/device-login/", {"email": email.strip(), "password": password, "device_name": device_name.strip()}, str(uuid.uuid4()))
                    api.token = result["token"]
                    vault.set("device-token", result["token"])
                    vault.set("device-expires", result["expires_at"])
                    user = result["user"]
                    store.put("meta", "user", user)
                offline = False
                try:
                    config, contracts = api.request("GET", "tracker/config/"), api.contracts()
                    store.put("meta", "config", config)
                    store.put("meta", "contracts", contracts)
                except ApiError as exc:
                    if not cached or not exc.retryable:
                        raise
                    config, contracts = store.get("meta", "config"), store.get("meta", "contracts")
                    if not config or contracts is None:
                        raise ValueError("Önbellekte sözleşme ve politika yok. İlk giriş çevrimiçi yapılmalıdır.") from exc
                    offline = True
                # Authentication and encryption checks run before this store is offered to capture.
                for kind in ("start", "grant", "block", "draft", "image"):
                    store.rows(kind)
                return vault, store, api, user, config, contracts, offline
            except Exception:
                store.close()
                raise
        self.mode = "Güvenli cihaz girişi yapılıyor"
        self._submit("login", login)

    def _reauthenticate(self, password):
        if not self.store or self.current:
            raise ValueError("Yeniden giriş için takip duraklatılmalıdır.")
        def refresh():
            # Public device-login must not carry the previous allowlisted Bearer.
            login_api = ApiClient(self.api.base_url)
            try:
                result = login_api.request("POST", "auth/device-login/", {"email": self.user["email"], "password": password, "device_name": "STEP Tracker"}, str(uuid.uuid4()))
            finally:
                login_api.http.close()
            if result["user"]["id"] != self.user["id"]:
                raise ValueError("Aynı hesapla giriş yapılmalıdır.")
            self.vault.set("device-token", result["token"])
            self.vault.set("device-expires", result["expires_at"])
            self.api.token = result["token"]
            return result
        if not password:
            raise ValueError("Şifre gerekir.")
        self._submit("reauthenticate", refresh)

    def _refresh(self):
        if not self.api:
            return
        def refresh():
            config, contracts = self.api.request("GET", "tracker/config/"), self.api.contracts()
            self.store.put("meta", "config", config)
            self.store.put("meta", "contracts", contracts)
            return config, contracts
        self._submit("refresh", refresh)

    def _permissions(self):
        if self.current or "start" in self.jobs:
            raise ValueError("İzinleri değiştirmeden önce takibi duraklatın.")
        mac_permissions(request=True)
        self._monitors()

    def _monitors(self):
        if self.current:
            raise ValueError("Ekran seçimini değiştirmek için takibi duraklatın.")
        self.screens = monitors()
        if not self.screens:
            raise CapabilityError("Fiziksel ekran bulunamadı; takip başlatılamaz.")
        self.monitor_list.emit(self.screens)

    def _start(self, contract_id, memo, monitor_id):
        if self.current or "start" in self.jobs:
            raise ValueError("Takip zaten açık veya sunucu yetkisi bekliyor.")
        if not self.store:
            raise ValueError("Önce cihaz girişi gerekir.")
        self._validate_policy()
        if self._unclosed():
            raise ValueError("Önce önceki yetkinin kayıtları, gizlilik işlemleri ve kapatması senkronize edilmelidir.")
        contract = next((c for c in self.contracts if c["id"] == contract_id), None)
        if not contract or not contract.get("tracker_ready"):
            raise ValueError("Sözleşme takip için hazır değil. Fon/limit durumunu yenileyin.")
        if not memo.strip():
            raise ValueError("Bu çalışma için kısa bir açıklama yazın.")
        current_screens = monitors()
        monitor = next((m for m in current_screens if m.id == monitor_id), None)
        if not monitor:
            raise CapabilityError("Seçili fiziksel ekran bulunamadı. Ekranları yenileyin.")
        self.resume_activity = None
        self._probe_native(monitor)
        self.selection = {"contract_id": contract_id, "memo": memo.strip(), "monitor": monitor}
        self.continuing = True
        self._request_grant()

    def _validate_policy(self):
        if not self.config or self.config.get("supported") is False:
            raise ValueError("Sunucu native takip desteğini kapatmış; kayıt başlatılamaz.")
        idle = self.config.get("idle_seconds")
        if not isinstance(idle, int) or isinstance(idle, bool) or idle <= 0:
            raise ValueError("Sunucunun hareketsizlik politikası yapılandırılmamış. Yönetici idle_seconds değerini ayarlamalıdır.")
        return idle

    def _clear_idle(self):
        self.idle_waiting = False
        self.idle_marker = None
        self.idle_resume_requested = False

    def _probe_native(self, monitor, last_activity=None):
        # Both explicit start and automatic grant renewal use this cleanup boundary.
        # Probe bytes are never retained and a failure requires explicit user resume.
        self.continuing = False
        self._clear_idle()
        if self.counters:
            self.counters.stop()
            self.counters = None
        # A technical grant renewal/probe is not a new human input event.
        counters = Counters(last_activity=last_activity)
        self.counters = counters
        try:
            counters.start()
            screenshot(monitor)
            active_app()
        except Exception:
            try:
                counters.stop()
            finally:
                self.counters = None
                self.continuing = False
                self.resume_activity = None
            raise

    def _request_grant(self):
        self._validate_policy()
        if self._unclosed():
            return
        if not self.counters:
            self._probe_native(self.selection["monitor"], last_activity=self.resume_activity)
            self.continuing = True
        ident = str(uuid.uuid4())
        payload = {"contract": self.selection["contract_id"], "memo": self.selection["memo"], "client_id": ident,
                   "monitor_id": self.selection["monitor"].id,
                   "capabilities": {"screen_capture": True, "input_counting": True, "active_app": True},
                   "requested_seconds": 600}
        self.store.put("start", ident, {"payload": payload, "resolved": False})
        self.mode = "Sunucudan ayrılmış fon ve süre yetkisi bekleniyor"
        self._submit("start", lambda: start_request(self.store, self.api, ident), ident)

    def _unclosed(self):
        return any(not r.get("resolved") for _, r in self.store.rows("start")) or any(not r.get("stopped") for _, r in self.store.rows("grant")) or any(not r.get("acknowledged") for _, r in self.store.rows("block"))

    def _activate(self, grant):
        self.server_mode = grant.get("mode")
        if not self.continuing:
            if self.counters:
                self.counters.stop()
                self.counters = None
            self.mode = "Sunucu yetkisi kapatılıyor; kayıt başlamadı"
            self._sync()
            return
        self.counters.check()
        application = active_app()
        now, mono = utc_now(), time.monotonic()
        if now < timestamp(grant["started_at"]) - timedelta(seconds=2):
            raise ValueError("Cihaz saati sunucudan geri. Otomatik tarih/saat eşitlemesini açıp yeniden deneyin.")
        available = min(600, int(grant["reserved_seconds"]) - int(grant["used_seconds"]),
                        (timestamp(grant["authorized_until"]) - now).total_seconds())
        if available < 1:
            self.continuing = False
            self.resume_activity = None
            self._clear_idle()
            self.counters.stop()
            self.counters = None
            self.mode = "Sunucu yetkisi sona erdi; ücretli kayıt başlamadı. Elle devam gerekir."
            self._sync()
            return
        self.store.update("grant", grant["id"], lambda r: r.update(close_requested=False))
        ident = str(uuid.uuid4())
        keys, mouse, _ = self.counters.snapshot()
        self.current = {"id": ident, "grant": grant, "mono": mono, "start": now,
                        "cap": available,
                        # A random point in the first three quarters leaves an OS-capture margin.
                        "offset": random.SystemRandom().uniform(0, available * 0.75),
                        "safe_mono": mono, "previous_tick": mono,
                        "base_keys": keys, "base_mouse": mouse, "image_id": None,
                        "captured_at": None, "active_app": application}
        self.mode = "Kayıt açık — yalnız sunucunun bu cihaza ayırdığı yetki"
        self.last_checkpoint = 0
        self._checkpoint()

    def _tick(self):
        current = self.current
        now = time.monotonic()
        keys, mouse, last = self.counters.snapshot()
        if now - current["previous_tick"] > 2:
            self._finish(current["safe_mono"], "Yerel takip işçisi kesildi; gözlenmeyen süre eklenmedi. Açıkça devam edin.", False)
            return
        current["previous_tick"] = now
        elapsed = now - current["mono"]
        idle = self._validate_policy()
        if now - last >= idle:
            self._finish(max(current["mono"], last),
                         "Hareketsizlikte bekliyor; yeni etkinlik ve ACK/fon kontrolü sonrası otomatik devam eder",
                         False, idle_snapshot=(keys, mouse, last))
            return
        # Check both the monotonic reserved budget and current authoritative expiry.
        until = (timestamp(current["grant"]["authorized_until"]) - utc_now()).total_seconds()
        if elapsed >= current["cap"] or until <= 0:
            cut = min(now, current["mono"] + current["cap"])
            if until <= 0:
                cut = min(cut, now + until)
            if current["image_id"] is None:
                self._finish(current["safe_mono"], "Bölüm görüntüsü alınamadı; tam bölüm tamamlanmadı. OS izinlerini kontrol edip açıkça devam edin.", False)
            else:
                self._finish(max(current["mono"], cut), "Yetki kullanıldı; yükleme ve kapatma ardından çevrimiçi yeni yetki beklenecek", True)
            return
        if now - self.last_native >= 1:
            self.counters.check()
            current["active_app"] = active_app()
            if not any(m.id == self.selection["monitor"].id and m.region == self.selection["monitor"].region for m in monitors()):
                raise CapabilityError("Seçili ekran değişti veya bağlantısı kesildi. Kayıt durduruldu.")
            current["safe_mono"] = now
            self.last_native = now
        if current["image_id"] is None and elapsed >= current["offset"]:
            png = screenshot(self.selection["monitor"])
            capture_mono = time.monotonic()
            # Slow/failed captures outside the grant never enter a billed segment.
            if capture_mono - current["mono"] >= current["cap"] or utc_now() >= timestamp(current["grant"]["authorized_until"]):
                self._finish(current["safe_mono"], "Ekran yakalama sırasında yetki sona erdi; yalnız son doğrulanan süre kaydedildi", False)
                return
            self.store.put("image", current["id"], {"png": base64.b64encode(png).decode()})
            current["image_id"] = current["id"]
            current["captured_at"] = iso(current["start"] + timedelta(seconds=capture_mono - current["mono"]))
            del png
            self._checkpoint()
        if now - self.last_checkpoint >= 1:
            self._checkpoint()

    def _idle_tick(self):
        # Idle retains only content-free input counters. No screen capture, active-app
        # query, draft checkpoint or billed time is created in this waiting state.
        self._validate_policy()
        if not self.counters or self.idle_marker is None:
            raise CapabilityError("Hareketsizlik sayacı kapandı; otomatik devam iptal edildi.")
        now = time.monotonic()
        if now - self.last_native >= 1:
            self.counters.check()
            self.last_native = now
        _, _, last = self.counters.snapshot()
        if last > self.idle_marker:
            self.idle_resume_requested = True
        if not self.idle_resume_requested:
            return
        if self._unclosed():
            self.mode = "Yeni etkinlik algılandı; önceki kayıt, gizlilik ve kapatma ACK'leri bekleniyor"
            if not any(k in self.jobs for k in ("start", "sync")):
                self._sync()
            return
        # Resuming is a new online grant, never reuse of an expired/shared budget.
        # Leave idle before the real screen/app capability probe. Probe failure
        # clears listeners/continuation and cannot restart on later input or sync.
        self._clear_idle()
        self._probe_native(self.selection["monitor"], last_activity=last)
        self.continuing = True
        self._request_grant()

    def _record(self, cut, snapshot=None):
        current = self.current
        duration = max(0, min(600, current["cap"], cut - current["mono"]))
        keys, mouse, last = snapshot if snapshot is not None else self.counters.snapshot()
        end = current["start"] + timedelta(seconds=duration)
        payload = {"client_id": current["id"], "session": current["grant"]["id"],
                   "starts_at": iso(current["start"]), "ends_at": iso(end), "seconds": math.floor(duration),
                   "key_count": max(0, keys - current["base_keys"]), "mouse_count": max(0, mouse - current["base_mouse"]),
                   "active_app": current["active_app"]}
        image_id = current["image_id"]
        if image_id and timestamp(current["captured_at"]) <= end:
            payload["captured_at"] = current["captured_at"]
        else:
            image_id = None
        return {"payload": payload, "image_id": image_id, "actions": [], "dispatched": False,
                "acknowledged": False, "result": None,
                "last_activity_seconds": max(0, min(duration, last - current["mono"]))}

    def _checkpoint(self):
        self.store.put("draft", self.current["id"], self._record(time.monotonic()))
        self.last_checkpoint = time.monotonic()

    def _finish(self, cut, message, auto_continue, idle_snapshot=None):
        if not self.current:
            return
        current = self.current
        snapshot = idle_snapshot if idle_snapshot is not None else self.counters.snapshot()
        record = self._record(cut, snapshot)
        ident, grant_id = current["id"], current["grant"]["id"]
        if idle_snapshot is None:
            self.counters.stop()
            self.counters = None
        self.current = None
        self.continuing = auto_continue and self.continuing
        self.resume_activity = snapshot[2] if self.continuing else None
        self._clear_idle()
        if idle_snapshot is not None:
            self.idle_waiting = True
            self.idle_marker = idle_snapshot[2]
        if record["payload"]["seconds"] > 0:
            # Block creation and grant final-ID membership are one local transaction.
            self.store.promote(ident, record, grant_id)
        else:
            self.store.remove_draft(ident)
        self.store.update("grant", grant_id, lambda r: r.update(close_requested=True))
        if current.get("image_id") and record.get("image_id") is None:
            self.store.release_image_copy(current["image_id"])
        self.mode = message
        self._sync()

    def _pause(self):
        self._clear_idle()
        self.resume_activity = None
        self.continuing = False
        if self.current:
            self._finish(time.monotonic(), "Takip duraklatıldı; Devam açıkça seçilmelidir", False)
        elif self.counters:
            self.counters.stop()
            self.counters = None
            self.mode = "Kullanıcı duraklattı; otomatik devam kapalı. Başlat/Devam seçilmelidir."

    def _stop(self):
        self._pause()
        self.mode = "Takip durdu; sunucu kapatması bütün kayıt ve gizlilik ACK'lerini bekler"
        self._sync()

    def _sync(self):
        if self.store and "start" not in self.jobs:
            if self._submit("sync", lambda: reconcile(self.store, self.api, self.cancelled)):
                self.last_sync = time.monotonic()
                self.sync_message = "Şifreli kuyruk sunucuyla uzlaştırılıyor"

    def _privacy(self, ident, reason):
        if not reason.strip():
            raise ValueError("Kişisel bilgi talebinin gerekçesini yazın.")
        def intent(record):
            if not record.get("image_id"):
                raise ValueError("Bu bölümde görüntü yok.")
            actions = record.get("actions", [])
            if any(a["operation"] in ("publish", "review-ready") and a["state"] != "done" for a in actions):
                raise ValueError("Yayın/önizleme işleminin sunucu sonucu bekleniyor. Sonuç bilinmeden yeni eylem gönderilemez.")
            screenshot_info = (record.get("result") or {}).get("screenshot") or {}
            if screenshot_info.get("state") in ("released", "withheld"):
                raise ValueError("Bu görüntünün yayın kararı daha önce gönderildi. Web destek/itiraz akışını kullanın.")
            if record["payload"].get("privacy_intent") or any(a["operation"] == "privacy" for a in actions):
                raise ValueError("Bu görüntü için kişisel bilgi talebi zaten kaydedilmiş.")
            if not record.get("dispatched"):
                record["payload"].update(privacy_intent=True, privacy_reason=reason.strip())
            else:
                record.setdefault("actions", []).append({"id": str(uuid.uuid4()), "operation": "privacy",
                                                         "payload": {"reason": reason.strip()}, "state": "pending"})
            record["acknowledged"] = False
        self.store.update("block", ident, intent)
        self._sync()
        self._emit()

    def _publication(self, ident, operation):
        if operation not in ("publish", "review-ready"):
            raise ValueError("Geçersiz görüntü eylemi.")
        def intent(record):
            screenshot_info = (record.get("result") or {}).get("screenshot") or {}
            if not screenshot_info.get("id"):
                raise ValueError("Önce görüntünün sunucu yüklemesi doğrulanmalıdır.")
            if screenshot_info.get("state") != "preview" or screenshot_info.get("publication_ready_at"):
                raise ValueError("Bu görüntü yayın/inceleme için artık beklemiyor.")
            if record["payload"].get("privacy_intent") or any(a["operation"] == "privacy" for a in record.get("actions", [])):
                raise ValueError("Kişisel bilgi talebi olan görüntü öğrenci tarafından yayımlanamaz.")
            if any(a["state"] != "done" for a in record.get("actions", [])):
                raise ValueError("Önce bekleyen görüntü işlemi sonuçlanmalıdır.")
            record.setdefault("actions", []).append({"id": str(uuid.uuid4()), "operation": operation, "payload": {}, "state": "pending"})
            record["acknowledged"] = False
        self.store.update("block", ident, intent)
        self._sync()
        self._emit()

    def _preview(self, ident):
        record = self.store.get("block", ident)
        if not record:
            raise ValueError("Görüntü kaydı bulunamadı.")
        image = self.store.get("image", record.get("image_id")) if record.get("image_id") else None
        if image:
            self.preview.emit({"ident": ident, "png": base64.b64decode(image["png"], validate=True)})
        else:
            screenshot_info = (record.get("result") or {}).get("screenshot")
            if not screenshot_info:
                raise ValueError("Bu bölümde ekran görüntüsü yok.")
            self._submit("preview", lambda: self.api.request("GET", f"screenshots/{screenshot_info['id']}/image/", binary=True), ident)

    def _quit(self):
        self._clear_idle()
        self.resume_activity = None
        self.continuing = False
        if self.current:
            self._finish(time.monotonic(), "Kapatılıyor; kuyruk şifreli olarak korunur", False)
        self.cancelled.set()
        self.quitting = True

    def _recover(self):
        for ident, draft in self.store.rows("draft"):
            payload = draft["payload"]
            # A crash cannot turn an unobserved idle gap into paid time.
            duration = min(payload["seconds"], math.floor(draft.get("last_activity_seconds", 0)))
            payload["seconds"] = duration
            payload["ends_at"] = iso(timestamp(payload["starts_at"]) + timedelta(seconds=duration))
            if draft.get("image_id") and timestamp(payload["captured_at"]) > timestamp(payload["ends_at"]):
                draft["image_id"] = None
                payload.pop("captured_at", None)
            if duration > 0:
                self.store.promote(ident, draft, payload["session"])
            else:
                self.store.remove_draft(ident)
        for ident, record in self.store.rows("grant"):
            self.server_mode = record["grant"].get("mode")
            self.store.update("grant", ident, lambda r: r.update(close_requested=True))
        referenced = {r.get("image_id") for _, r in self.store.rows("block")}
        for ident, _ in self.store.rows("image"):
            if ident not in referenced:
                self.store.release_image_copy(ident)

    def _poll_jobs(self):
        for kind, (future, context) in list(self.jobs.items()):
            if not future.done():
                continue
            del self.jobs[kind]
            try:
                result = future.result()
                if kind == "login":
                    self.vault, self.store, self.api, self.user, self.config, self.contracts, offline = result
                    self._recover()
                    self.mode = "Önbellek açık; yeni kayıt için çevrimiçi yetki gerekir" if offline else "Takip için hazır"
                    self.authenticated.emit({"user": self.user, "contracts": self.contracts})
                    try:
                        self._monitors()
                    except CapabilityError as exc:
                        self.error.emit(str(exc))
                    self._sync()
                elif kind == "start":
                    self._activate(result)
                elif kind == "sync":
                    self.sync_message = "Bütün gönderimler doğrulandı" if not result else result[0]["message"] + " [" + result[0]["code"] + "]"
                    if result:
                        if not self.current or any(e.get("status") == 401 for e in result):
                            self._fail("Senkronizasyon/auth hatası; otomatik devam kapalı. " + self.sync_message)
                        # Active offline work may continue only inside its existing
                        # grant. A paused/faulted tracker cannot restart itself.
                    elif self.continuing and not self.current and not self._unclosed():
                        self._request_grant()
                elif kind == "refresh":
                    self.config, self.contracts = result
                    self.authenticated.emit({"user": self.user, "contracts": self.contracts})
                elif kind == "preview":
                    self.preview.emit({"ident": context, "png": result})
                elif kind == "reauthenticate":
                    self.mode = "Cihaz girişi yenilendi"
                    self._refresh()
                    self._sync()
            except (StorageError, CapabilityError) as exc:
                # Native errors during sync-triggered renewal also stop listeners;
                # they must not fall through to network-only error presentation.
                self._fail(str(exc))
            except (ValueError, ApiError) as exc:
                self.sync_message = str(exc)
                if self.idle_waiting or kind in ("start", "sync") or (isinstance(exc, ApiError) and exc.status == 401):
                    self._fail("İşlem hatası; otomatik devam kapalı. " + str(exc))
                else:
                    self.error.emit(str(exc))
                    if not self.current:
                        self.mode = "İşlem bekliyor; şifreli kuyruk korunuyor"
            except Exception:
                self._fail("Sunucu veya yerel kayıt cevabı okunamadı; aynı işlem korunuyor.")

    def _fail(self, message):
        self._clear_idle()
        self.resume_activity = None
        self.continuing = False
        if self.current:
            try:
                self._finish(self.current["safe_mono"], message, False)
            except Exception:
                if self.counters:
                    self.counters.stop()
                self.current = self.counters = None
        elif self.counters:
            self.counters.stop()
            self.counters = None
        self.mode = message
        self.error.emit(message)

    def _emit(self):
        records = []
        if self.store:
            for ident, record in self.store.rows("block"):
                if not record.get("image_id"):
                    continue
                info = (record.get("result") or {}).get("screenshot") or {}
                actions = record.get("actions", [])
                pending = [a for a in actions if a["state"] != "done"]
                privacy = record["payload"].get("privacy_intent") or any(a["operation"] == "privacy" for a in actions)
                decision = any(a["operation"] in ("publish", "review-ready") for a in actions) or info.get("publication_ready_at")
                publication_pending = any(a["operation"] in ("publish", "review-ready") and a["state"] != "done" for a in actions)
                records.append({"id": ident, "at": record["payload"].get("captured_at"), "seconds": record["payload"]["seconds"],
                                "state": info.get("state", "Şifreli kuyruk"), "error": record.get("error"),
                                "privacy_pending": bool(privacy and not record.get("acknowledged")),
                                "can_privacy": not privacy and not publication_pending and info.get("state") not in ("released", "withheld") and not pending,
                                "can_publish": bool(info.get("id")) and info.get("state") == "preview" and not privacy and not decision and not pending})
        elapsed = min(self.current["cap"], time.monotonic() - self.current["mono"]) if self.current else 0
        grant = self.current["grant"] if self.current else None
        self.changed.emit({"mode": self.mode, "server_mode": self.server_mode, "sync": self.sync_message, "recording": bool(self.current),
                           "starting": "start" in self.jobs, "idle_waiting": self.idle_waiting,
                           "idle_resume_requested": self.idle_resume_requested,
                           "elapsed": max(0, math.floor(elapsed)),
                           "remaining": max(0, math.floor(self.current["cap"] - elapsed)) if self.current else None,
                           "funding": grant.get("funding") if grant else None,
                           "authorized_until": grant.get("authorized_until") if grant else None,
                           "pending": self.store.pending() if self.store else 0,
                           "screenshots": records[-100:][::-1], "idle_seconds": self.config.get("idle_seconds") if self.config else None,
                           "preview_seconds": self.config.get("preview_seconds") if self.config else None})
