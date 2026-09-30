"""OS keyring and an authenticated, encrypted SQLite outbox; no PNG temp files."""
import base64
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import threading
from pathlib import Path

import keyring
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from platformdirs import user_data_dir

from .api import canonical


class StorageError(Exception):
    pass


class Vault:
    def __init__(self, base_url, email):
        self.account = hashlib.sha256((base_url + "\n" + email.strip().casefold()).encode()).hexdigest()
        self.service = "STEP Tracker " + self.account
        backend = keyring.get_keyring()
        candidates = getattr(backend, "backends", [backend])
        allowed = ("keyring.backends.macOS", "keyring.backends.Windows", "keyring.backends.SecretService", "keyring.backends.kwallet")
        secure = [b for b in candidates if type(b).__module__.startswith(allowed) and b.priority > 0]
        if not secure:
            raise StorageError("Güvenli işletim sistemi anahtarlığı bulunamadı. Plaintext depolama kullanılmayacak.")
        self.backend = secure[0]
        try:
            probe = secrets.token_hex(16)
            self.backend.set_password(self.service, "probe", probe)
            if self.backend.get_password(self.service, "probe") != probe:
                raise StorageError("İşletim sistemi anahtarlığı doğrulanamadı.")
            self.backend.delete_password(self.service, "probe")
        except Exception as exc:
            raise StorageError("İşletim sistemi anahtarlığı kilitli veya kullanılamıyor.") from exc

    def get(self, name):
        try:
            return self.backend.get_password(self.service, name)
        except Exception as exc:
            raise StorageError("Anahtarlığa erişilemiyor; kayıt başlatılmadı.") from exc

    def set(self, name, value):
        try:
            self.backend.set_password(self.service, name, value)
        except Exception as exc:
            raise StorageError("Güvenli anahtarlığa yazılamadı.") from exc

    def queue_key(self):
        encoded = self.get("queue-key")
        if not encoded:
            encoded = base64.b64encode(AESGCM.generate_key(bit_length=256)).decode()
            self.set("queue-key", encoded)
        return base64.b64decode(encoded, validate=True)


class EncryptedStore:
    def __init__(self, vault):
        folder = Path(user_data_dir("STEP Tracker", "STEP")) / vault.account
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform != "win32":
            folder.chmod(0o700)
        self.path = folder / "outbox.sqlite3"
        self.aes = AESGCM(vault.queue_key())
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.execute("CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL, id TEXT NOT NULL, data BLOB NOT NULL, PRIMARY KEY(kind,id))")
        self.db.commit()
        if sys.platform != "win32":
            self.path.chmod(0o600)

    def _decode(self, kind, ident, data):
        try:
            return json.loads(self.aes.decrypt(data[:12], data[12:], (kind + ":" + ident).encode()))
        except Exception as exc:
            raise StorageError("Şifreli kayıt doğrulanamadı. Veri değiştirilmedi; takip başlatılamaz.") from exc

    def get(self, kind, ident):
        with self.lock:
            row = self.db.execute("SELECT data FROM records WHERE kind=? AND id=?", (kind, ident)).fetchone()
            return self._decode(kind, ident, row[0]) if row else None

    def put(self, kind, ident, value):
        with self.lock:
            nonce = os.urandom(12)
            encrypted = nonce + self.aes.encrypt(nonce, canonical(value), (kind + ":" + ident).encode())
            self.db.execute("INSERT INTO records(kind,id,data) VALUES(?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data", (kind, ident, encrypted))
            self.db.commit()

    def update(self, kind, ident, change):
        with self.lock:
            value = self.get(kind, ident)
            if value is None:
                raise StorageError("Şifreli kuyruk kaydı bulunamadı.")
            result = change(value)
            self.put(kind, ident, value)
            return result

    def rows(self, kind):
        with self.lock:
            rows = self.db.execute("SELECT id,data FROM records WHERE kind=? ORDER BY rowid", (kind,)).fetchall()
            return [(ident, self._decode(kind, ident, data)) for ident, data in rows]

    def remove_draft(self, ident):
        # Internal checkpoint promotion only. The student has no delete operation.
        with self.lock:
            self.db.execute("DELETE FROM records WHERE kind='draft' AND id=?", (ident,))
            self.db.commit()

    def pending(self):
        return sum(not r.get("acknowledged") for _, r in self.rows("block")) + sum(not r.get("stopped") for _, r in self.rows("grant")) + sum(not r.get("resolved") for _, r in self.rows("start"))

    def close(self):
        with self.lock:
            self.db.close()

    def promote(self, ident, record, grant_id):
        """Commit complete block, final-ID membership and draft removal together."""
        with self.lock:
            grant = self.get("grant", grant_id)
            if not grant:
                raise StorageError("Yerel sunucu yetkisi bulunamadı; bölüm değiştirilmedi.")
            if ident not in grant["final_client_ids"]:
                grant["final_client_ids"].append(ident)
            sealed = []
            for kind, row_id, value in (("block", ident, record), ("grant", grant_id, grant)):
                nonce = os.urandom(12)
                sealed.append((kind, row_id, nonce + self.aes.encrypt(nonce, canonical(value), (kind + ":" + row_id).encode())))
            try:
                self.db.execute("BEGIN IMMEDIATE")
                for values in sealed:
                    self.db.execute("INSERT INTO records(kind,id,data) VALUES(?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data", values)
                self.db.execute("DELETE FROM records WHERE kind='draft' AND id=?", (ident,))
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise StorageError("Yerel kayıt atomik tamamlanamadı; önceki şifreli bölüm korundu.")

    def release_image_copy(self, ident):
        # Internal outbox/cache cleanup after server ACK, never a student delete control.
        with self.lock:
            self.db.execute("DELETE FROM records WHERE kind='image' AND id=?", (ident,))
            self.db.commit()
