"""Verified HTTPS, scoped device auth and deterministic mutation bytes."""
import base64
import ipaddress
import json
from urllib.parse import urlsplit, urlunsplit

import requests


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def backend_url(value, local_development=False):
    parts = urlsplit(value.strip())
    if not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Backend adresi kullanıcı bilgisi, sorgu veya parça içermemelidir.")
    loopback = parts.hostname.lower() == "localhost"
    try:
        loopback = loopback or ipaddress.ip_address(parts.hostname).is_loopback
    except ValueError:
        pass
    if parts.scheme != "https" and not (parts.scheme == "http" and loopback and local_development):
        raise ValueError("HTTPS gerekir. HTTP yalnız açıkça seçilen localhost geliştirmesinde kullanılabilir.")
    path = parts.path.rstrip("/")
    if path not in ("", "/api/v1"):
        raise ValueError("Backend kök adresini veya /api/v1 adresini girin.")
    return urlunsplit((parts.scheme, parts.netloc, "/api/v1/", "", ""))


class ApiError(Exception):
    def __init__(self, code, message, retryable=False, status=None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.status = status


class ApiClient:
    def __init__(self, base_url, token=""):
        self.base_url = base_url
        self.token = token
        self.http = requests.Session()
        # Never silently use environment proxy credentials or an environment CA bypass.
        self.http.trust_env = False

    def request(self, method, path, payload=None, key=None, binary=False, multipart=False):
        if "://" in path or path.startswith("/") or ".." in path:
            raise ApiError("invalid_endpoint", "Geçersiz API yolu.")
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if key:
            headers["Idempotency-Key"] = key
        body = None
        if multipart:
            body, content_type = self.multipart(payload)
            headers["Content-Type"] = content_type
        elif payload is not None:
            body = canonical(payload)
            headers["Content-Type"] = "application/json; charset=utf-8"
        try:
            response = self.http.request(method, self.base_url + path, data=body,
                                         headers=headers, timeout=(8, 25), verify=True,
                                         allow_redirects=False)
        except requests.exceptions.SSLError as exc:
            raise ApiError("tls", "Sunucu sertifikası doğrulanamadı. TLS kontrolü kapatılmadı.") from exc
        except requests.exceptions.RequestException as exc:
            raise ApiError("transport_unknown", "Bağlantı kesildi; işlem sonucu bilinmiyor. Aynı kayıt korunuyor.", True) from exc
        if not 200 <= response.status_code < 300:
            try:
                error = response.json()
            except ValueError:
                error = {}
            code = error.get("code", f"http_{response.status_code}") if isinstance(error, dict) else f"http_{response.status_code}"
            if not isinstance(code, str) or len(code) > 80 or not all(c.isalnum() or c == "_" for c in code):
                code = f"http_{response.status_code}"
            # Do not put raw HTML, request bodies, credentials or proxy diagnostics into UI/logs.
            labels = {
                401: "Cihaz oturumu sona ermiş veya iptal edilmiş. Aynı hesapla yeniden giriş yapın.",
                403: "İşlem için izin yok; kayıt silinmedi.",
                409: "Sunucu işlem/fon/limit çakışması bildirdi; kayıt korunuyor.",
                429: "İstek sınırına ulaşıldı. Daha sonra tekrar deneyin.",
            }
            domain_labels = {
                "unfunded": "Yeni çalışma için ön fon yok. Fon tamamlanana kadar aynı başlatma kaydı bekler.",
                "weekly_limit": "Ortak haftalık süre limiti doldu. Yeni ücretli kayıt başlamadı.",
                "open_session": "Önceki cihaz çalışma yetkisi açık. Kayıtları senkronize edip kapatın.",
                "idempotency_processing": "Sunucu aynı işlemi hâlâ işliyor. Aynı UUID ile sonuç bekleniyor.",
                "idempotency_conflict": "Sunucu aynı UUID için farklı istek gördü; şifreli kayıt korunuyor.",
                "period_closed": "Hafta kapandı; çevrimdışı kayıt destek incelemesi gerektiriyor. Veri korunuyor.",
                "milestone_closed": "İş aşaması kapandı; bekleyen kayıt destek incelemesi gerektiriyor.",
                "image_published": "Görüntü artık yayın öncesi durumda değil; talep kabul edilmedi. STEP destek akışını kullanın.",
            }
            message = domain_labels.get(code, labels.get(response.status_code, "Sunucu isteği kabul etmedi; kayıt korunuyor."))
            raise ApiError(code, message, response.status_code >= 500 or response.status_code in (409, 429), response.status_code)
        if binary:
            return response.content
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError("invalid_response", "Sunucu cevabı okunamadı; işlem sonucu yeniden uzlaştırılmalıdır.", True) from exc

    @staticmethod
    def multipart(record):
        # Stable boundary, ordering and file bytes allow exact immutable timeout retries.
        block = record["payload"]
        boundary = "step-" + block["client_id"]
        chunks = []
        for name, value in sorted(block.items()):
            if value is None:
                continue
            if isinstance(value, bool):
                value = "true" if value else "false"
            chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                           f'{value}\r\n').encode("utf-8"))
        if record.get("png"):
            chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="screenshot"; '
                           'filename="capture.png"\r\nContent-Type: image/png\r\n\r\n').encode())
            chunks.append(base64.b64decode(record["png"], validate=True))
            chunks.append(b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode())
        return b"".join(chunks), "multipart/form-data; boundary=" + boundary

    def contracts(self):
        rows, page = [], 1
        while True:
            value = self.request("GET", f"tracker/contracts/?page={page}&page_size=100")
            rows.extend(value["results"])
            if not value.get("next"):
                return rows
            page += 1
