"""Prepare actual STEP local environment, preserving existing values. No secrets printed."""
import base64
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"

def main():
    existing = ENV.read_text() if ENV.exists() else ""
    keys = {line.split("=", 1)[0].strip() for line in existing.splitlines() if "=" in line and not line.lstrip().startswith("#")}
    values = {
        "STEP_MODE": "test", "STEP_DEBUG": "1", "STEP_PAYMENT_PROVIDER": "simulator",
        "STEP_SECRET_KEY": secrets.token_urlsafe(64),
        "STEP_FIELD_ENCRYPTION_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "STEP_DB_NAME": "step", "STEP_DB_USER": "step", "STEP_DB_PASSWORD": secrets.token_urlsafe(40),
        "STEP_DB_HOST": "db", "STEP_DB_PORT": "5432", "STEP_PRIVATE_ROOT": "/app/private",
        "STEP_ALLOWED_HOSTS": "localhost,127.0.0.1", "STEP_COOKIE_SAMESITE": "Lax",
        "STEP_WEB_ORIGINS": "http://localhost:3001", "STEP_WEB_URL": "http://localhost:3001",
        "STEP_API_URL": "http://localhost:8002", "NEXT_PUBLIC_STEP_API_URL": "http://localhost:8002/api/v1/",
        "STEP_DEVICE_TOKEN_SECONDS": "2592000", "STEP_UPLOAD_MAX_BYTES": "20971520",
        "STEP_SMTP_HOST": "", "STEP_SMTP_PORT": "587", "STEP_SMTP_USER": "",
        "STEP_SMTP_PASSWORD": "", "STEP_SMTP_TLS": "1", "STEP_SMTP_FROM": "",
        "STEP_IYZICO_API_KEY": "", "STEP_IYZICO_SECRET_KEY": "", "STEP_SERVER_PUBLIC_IP": "",
        "STEP_NETGSM_USER": "", "STEP_NETGSM_PASSWORD": "", "STEP_NETGSM_HEADER": "",
    }
    additions = "".join(f"{key}='{value}'\n" for key, value in values.items() if key not in keys)
    ENV.write_text(existing + ("\n" if existing and not existing.endswith("\n") else "") + additions)
    os.chmod(ENV, 0o600)
    print("STEP actual .env prepared; existing values preserved. Provider/SMTP values remain unset unless previously configured.")

if __name__ == "__main__":
    main()
