"""Capture and event counters start only after an explicit user start command."""
import ctypes
import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import PureWindowsPath

from mss import MSS
from mss.tools import to_png


class CapabilityError(Exception):
    pass


@dataclass(frozen=True)
class Monitor:
    id: str
    label: str
    left: int
    top: int
    width: int
    height: int

    @property
    def region(self):
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


def require_platform():
    if sys.platform == "linux":
        if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" or os.environ.get("WAYLAND_DISPLAY"):
            raise CapabilityError("Wayland tam etkinlik kaydını desteklemiyor. Çıkış yapıp X11/Xorg oturumu seçin.")
        if not os.environ.get("DISPLAY"):
            raise CapabilityError("Linux takip için açık bir X11 masaüstü oturumu gerekir.")
    elif sys.platform not in ("win32", "darwin"):
        raise CapabilityError("Bu işletim sistemi desteklenmiyor.")


def mac_permissions(request=False):
    if sys.platform != "darwin":
        return
    import Quartz
    from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
    if request:
        Quartz.CGRequestScreenCaptureAccess()
        Quartz.CGRequestListenEventAccess()
    trusted = AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: request})
    if not Quartz.CGPreflightScreenCaptureAccess():
        raise CapabilityError("Sistem Ayarları → Gizlilik ve Güvenlik → Ekran Kaydı: STEP Tracker iznini açın.")
    if not Quartz.CGPreflightListenEventAccess() or not trusted:
        raise CapabilityError("Gizlilik ve Güvenlik → Giriş İzleme / Erişilebilirlik: STEP Tracker iznini açın ve uygulamayı yeniden başlatın.")


def monitors():
    require_platform()
    mac_permissions()
    with MSS() as capture:
        rows = capture.monitors[1:]
        return [Monitor(str(getattr(m, "unique_id", None) or f"{m.left}:{m.top}:{m.width}:{m.height}"),
                        f"Ekran {index + 1} — {m.width}×{m.height}", m.left, m.top, m.width, m.height)
                for index, m in enumerate(rows)]


def screenshot(monitor):
    require_platform()
    mac_permissions()
    current = next((m for m in monitors() if m.id == monitor.id and m.region == monitor.region), None)
    if current is None:
        raise CapabilityError("Seçili ekran ayrılmış veya düzeni değişmiş. Takip durdu; ekranı yeniden seçin.")
    with MSS() as capture:
        image = capture.grab(current.region)
        return to_png(image.rgb, image.size)


def app_identifier(value):
    if value is None:
        raise CapabilityError("Aktif uygulama kimliği bulunamadı; ücretli kayıt durduruldu.")
    value = str(value)
    if not value or any(c in value for c in ("/", "\\", "\n", "\r")):
        raise CapabilityError("Yalnız uygulama kimliği okunmalıdır; geçersiz OS uygulama bilgisi kaydedilmedi.")
    return value[:160]


def active_app():
    require_platform()
    try:
        if sys.platform == "darwin":
            from AppKit import NSWorkspace
            from Foundation import NSAutoreleasePool
            pool = NSAutoreleasePool.alloc().init()
            try:
                app = NSWorkspace.sharedWorkspace().frontmostApplication()
                if app is None:
                    raise CapabilityError("Aktif uygulama okunamıyor; kayıt durduruldu.")
                return app_identifier(app.bundleIdentifier() or app.localizedName())
            finally:
                pool.drain()
        if sys.platform == "win32":
            from ctypes import wintypes
            user32, kernel32 = ctypes.WinDLL("user32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
            user32.GetForegroundWindow.restype = wintypes.HWND
            user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            window = user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            if not window or not user32.GetWindowThreadProcessId(window, ctypes.byref(pid)):
                raise CapabilityError("Aktif uygulamaya erişilemiyor; kayıt durduruldu.")
            handle = kernel32.OpenProcess(0x1000, False, pid.value)
            if not handle:
                raise CapabilityError("Aktif uygulamanın süreç izni yok; kayıt durduruldu.")
            try:
                size = wintypes.DWORD(32768)
                buffer = ctypes.create_unicode_buffer(size.value)
                if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                    raise CapabilityError("Aktif uygulama bilgisi okunamadı.")
                # Full path never reaches a persisted or emitted object.
                return app_identifier(PureWindowsPath(buffer.value).name)
            finally:
                kernel32.CloseHandle(handle)
        from Xlib import display
        connection = display.Display()
        try:
            prop = connection.screen().root.get_full_property(connection.intern_atom("_NET_ACTIVE_WINDOW"), 0)
            if prop is None or not len(prop.value) or not prop.value[0]:
                raise CapabilityError("X11 aktif uygulama bilgisi bulunamadı.")
            window = connection.create_resource_object("window", int(prop.value[0]))
            wm_class = window.get_wm_class()
            if not wm_class:
                raise CapabilityError("X11 uygulama sınıfı okunamadı.")
            return app_identifier(wm_class[-1])
        finally:
            connection.close()
    except CapabilityError:
        raise
    except Exception as exc:
        raise CapabilityError("Aktif uygulama bilgisi için işletim sistemi erişimi sağlanamadı.") from exc


class Counters:
    def __init__(self, last_activity=None):
        self.lock = threading.Lock()
        self.keys = self.mouse = 0
        self.last_activity = time.monotonic() if last_activity is None else last_activity
        self.keyboard = self.pointer = None

    def _key(self, _ignored):
        with self.lock:
            self.keys += 1
            self.last_activity = time.monotonic()

    def _mouse(self, *_ignored):
        # Coordinates, button identities and scroll deltas are never inspected/stored.
        with self.lock:
            self.mouse += 1
            self.last_activity = time.monotonic()

    def _click(self, _x, _y, _button, pressed):
        if pressed:
            self._mouse()

    def start(self):
        require_platform()
        mac_permissions()
        from pynput import keyboard, mouse
        self.keyboard = keyboard.Listener(on_press=self._key)
        self.pointer = mouse.Listener(on_move=self._mouse, on_click=self._click, on_scroll=self._mouse)
        if not self.keyboard.IS_TRUSTED or not self.pointer.IS_TRUSTED:
            raise CapabilityError("Klavye/fare etkinlik izni eksik; takip başlatılmadı.")
        self.keyboard.start()
        self.pointer.start()
        for listener in (self.keyboard, self.pointer):
            ready = threading.Event()
            def await_ready(current=listener, event=ready):
                current.wait()
                event.set()
            threading.Thread(target=await_ready, daemon=True).start()
            if not ready.wait(3) or not listener.is_alive():
                self.stop()
                raise CapabilityError("İşletim sistemi etkinlik sayacını başlatamadı. İzinleri kontrol edin.")
        self.check()

    def check(self):
        mac_permissions()
        if not self.keyboard or not self.pointer or not self.keyboard.is_alive() or not self.pointer.is_alive():
            raise CapabilityError("Etkinlik izleyicisi durdu; ücretli kayıt durduruldu.")
        if not self.keyboard.IS_TRUSTED or not self.pointer.IS_TRUSTED:
            raise CapabilityError("Etkinlik izleme izni kaldırıldı; kayıt durduruldu.")

    def snapshot(self):
        with self.lock:
            return self.keys, self.mouse, self.last_activity

    def stop(self):
        for listener in (self.keyboard, self.pointer):
            if listener:
                listener.stop()
                try:
                    listener.join(timeout=1)
                except Exception:
                    pass
        self.keyboard = self.pointer = None
