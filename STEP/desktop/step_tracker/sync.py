"""Single network-worker outbox reconciliation. Unknown mutations remain immutable."""
import hashlib
import uuid
from datetime import datetime, timezone

from .api import ApiError, ApiClient
from .storage import StorageError


def utc_now():
    return datetime.now(timezone.utc)


def iso(value):
    return value.isoformat(timespec="milliseconds")


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timezone required")
    return result.astimezone(timezone.utc)


def remember_grant(store, request_id, result):
    try:
        uuid.UUID(result["id"])
        reserved, used = int(result["reserved_seconds"]), int(result["used_seconds"])
        if reserved <= 0 or used < 0 or used > reserved:
            raise ValueError("Invalid grant")
        timestamp(result["authorized_until"])
        timestamp(result["started_at"])
        if not isinstance(result["funding"], dict):
            raise ValueError("Missing funding")
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError("invalid_grant", "Sunucu takip yetkisi okunamadı. Aynı başlatma isteği korunuyor.", True) from exc
    request = store.get("start", request_id)["payload"]
    if result.get("client_id") != request_id or result.get("contract") != request["contract"]:
        raise ApiError("invalid_grant", "Sunucu yetki kimliği uyuşmuyor; aynı başlatma kaydı korunuyor.", True)
    ident = result["id"]
    # A grant obtained while reconciling an unknown start never starts capturing by itself.
    if not store.get("grant", ident):
        store.put("grant", ident, {"grant": result, "final_client_ids": [], "close_requested": True,
                                  "stopped": False, "stop_key": str(uuid.uuid4())})
    store.update("start", request_id, lambda r: r.update(resolved=True, result=result))
    return result


def start_request(store, api, ident):
    record = store.get("start", ident)
    result = api.request("POST", "tracker/sessions/", record["payload"], ident)
    return remember_grant(store, ident, result)


def upload_record(store, record):
    image = store.get("image", record["image_id"]) if record.get("image_id") else None
    if record.get("image_id") and not image:
        raise StorageError("Gönderilmemiş görüntünün şifreli verisi eksik; kayıt korunuyor.")
    return {"payload": record["payload"], "png": image["png"] if image else None}


def record_error(store, kind, ident, error):
    store.update(kind, ident, lambda r: r.update(error={"code": error.code, "message": str(error)}))


def reconcile(store, api, cancelled=None):
    errors = []
    for ident, record in store.rows("start"):
        if cancelled and cancelled.is_set():
            return errors
        if record.get("resolved"):
            continue
        try:
            start_request(store, api, ident)
        except ApiError as exc:
            record_error(store, "start", ident, exc)
            if exc.status in (400, 401, 403, 404, 422):
                store.update("start", ident, lambda r: r.update(resolved=True, rejected=True))
            errors.append({"code": exc.code, "message": str(exc), "status": exc.status})
            if exc.status == 401:
                return errors

    for ident, original in store.rows("block"):
        if cancelled and cancelled.is_set():
            return errors
        record = store.get("block", ident)
        if record.get("acknowledged") and all(a["state"] == "done" for a in record.get("actions", [])):
            captured = record["payload"].get("captured_at")
            if record.get("image_id") and captured and (utc_now() - timestamp(captured)).total_seconds() >= 90 * 86400:
                store.release_image_copy(record["image_id"])
            continue
        try:
            if not record.get("result"):
                def freeze(value):
                    body, _ = ApiClient.multipart(upload_record(store, value))
                    digest = hashlib.sha256(body).hexdigest()
                    if value.get("digest") and value["digest"] != digest:
                        raise StorageError("Değişmez gönderim özeti uyuşmuyor; kayıt gönderilmedi.")
                    value.update(dispatched=True, digest=digest)
                    return upload_record(store, value)
                frozen = store.update("block", ident, freeze)
                result = api.request("POST", "tracker/blocks/", frozen, ident, multipart=True)
                if result.get("client_id") != ident or result.get("session") != record["payload"]["session"]:
                    raise ApiError("invalid_block", "Sunucu kayıt kimliği uyuşmuyor; gönderim uzlaştırılmalıdır.", True)
                if record.get("image_id"):
                    info = result.get("screenshot")
                    try:
                        uuid.UUID(info["id"])
                    except (TypeError, KeyError, ValueError) as exc:
                        raise ApiError("invalid_screenshot", "Yüklenen görüntünün sunucu kimliği doğrulanamadı; orijinal kayıt korunuyor.", True) from exc
                    if record["payload"].get("privacy_intent") and (info.get("state") != "held" or not info.get("privacy_request")):
                        raise ApiError("privacy_not_confirmed", "Atomik kişisel bilgi engeli doğrulanamadı; yayın açılmadı ve kayıt korunuyor.", True)
                store.update("block", ident, lambda r: r.update(result=result, error=None))

            while True:
                if cancelled and cancelled.is_set():
                    return errors
                record = store.get("block", ident)
                pending = next((a for a in record.get("actions", []) if a["state"] != "done"), None)
                if pending is None:
                    break
                screenshot = record["result"].get("screenshot")
                if not screenshot or not screenshot.get("id"):
                    raise ApiError("missing_screenshot", "Görüntü kimliği henüz doğrulanamadı; kişisel bilgi talebi bekliyor.", True)
                action_id = pending["id"]
                operation = pending["operation"]
                # Publication and privacy intents cannot pass each other in the queue.
                if operation != "privacy" and any(a["operation"] == "privacy" and a["state"] != "done" for a in record.get("actions", [])):
                    raise ApiError("privacy_pending", "Kişisel bilgi talebi tamamlanmadan yayın işlemi gönderilemez.")
                def dispatched(value):
                    action = next(a for a in value["actions"] if a["id"] == action_id)
                    action["state"] = "dispatched"
                store.update("block", ident, dispatched)
                result = api.request("POST", f"screenshots/{screenshot['id']}/{operation}/", pending["payload"], action_id)
                def completed(value):
                    next(a for a in value["actions"] if a["id"] == action_id)["state"] = "done"
                    if isinstance(result, dict):
                        updated = result.get("screenshot", result)
                        if updated.get("id") == screenshot["id"] and "state" in updated:
                            value["result"]["screenshot"].update(updated)
                    if operation == "privacy":
                        value["result"]["screenshot"]["state"] = "held"
                    elif operation == "publish":
                        value["result"]["screenshot"]["state"] = "released"
                    value["error"] = None
                store.update("block", ident, completed)
            def acknowledge(value):
                value["acknowledged"] = all(a["state"] == "done" for a in value.get("actions", []))
                value["error"] = None
            store.update("block", ident, acknowledge)
            settled = store.get("block", ident)
            # Confirmed owner actions or the local 90-day cache boundary release only
            # this encrypted copy; server case holds and time ledgers remain authoritative.
            captured = settled["payload"].get("captured_at")
            old_cache = captured and (utc_now() - timestamp(captured)).total_seconds() >= 90 * 86400
            if settled.get("acknowledged") and settled.get("image_id") and (settled.get("actions") or settled["payload"].get("privacy_intent") or old_cache):
                store.release_image_copy(settled["image_id"])
        except ApiError as exc:
            record_error(store, "block", ident, exc)
            errors.append({"code": exc.code, "message": str(exc), "status": exc.status})
            if exc.status == 401:
                return errors

    for ident, record in store.rows("grant"):
        if cancelled and cancelled.is_set():
            return errors
        if record.get("stopped") or not record.get("close_requested"):
            continue
        ids = record["final_client_ids"]
        if any(not (store.get("block", block_id) or {}).get("acknowledged") for block_id in ids):
            continue
        if any(r["payload"]["session"] == ident and not r.get("acknowledged") for _, r in store.rows("block")):
            continue
        try:
            api.request("POST", f"tracker/sessions/{ident}/stop/", {"final_client_ids": ids}, record["stop_key"])
            store.update("grant", ident, lambda r: r.update(stopped=True, error=None))
        except ApiError as exc:
            record_error(store, "grant", ident, exc)
            errors.append({"code": exc.code, "message": str(exc), "status": exc.status})
    return errors
