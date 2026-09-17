# C bağımsız review — backend_review — FAILED
Görev/dosyalar: c-review; FIRST/backend/accounts serializers/models/views/middleware/session/security/settings/migrations/tests.
Komut: cd FIRST/backend && .venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity 1 — 26 passed (0.390s).
Ek süreç içi probe: test_settings, memory SQLite migrate ve RegisterSerializer ile username="a\u0301b"; valid=True, normalized="áb", length=2.
P2 bulgu: serializers.py ProfileSerializer.username length validator NFC öncesinde; kabul edilmiş 3–30 karakter sınırı normalizasyon sonrası ihlal ediliyor. NFC önce uygulanmalı, alt ve üst sınır regresyonu eklenmeli. C kapısı FAILED, web başlamadı.
İlk ek belge okuması backend cwd nedeniyle root yollarını bulamadı; repo kökünden tekrar okuma geçti. Başka P1/P2 yok. Kaynak değiştirilmedi.
Yapılmayanlar: gerçek PostgreSQL/Redis/SMTP, browser/proxy/runtime/deploy not_verified; kullanıcı sınırı.
