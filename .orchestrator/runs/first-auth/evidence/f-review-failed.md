# F bağımsız review — backend_review — FAILED
Görev/dosyalar: f-review; accounts/models.py User.save(), F account views/token/limits/routes/tests.
Komut: .venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity1 —62 passed0.953s. Ek .venv/bin/python stdin probe memory migrations + actual django update_last_login signal.
P1: User.save(update_fields=...) her partial save'e email/username/normalized ekliyor. Eski instance okunur; DB email yeni verified adrese/version2 ilerler; update_last_login(None, stale) eski email'i geri yazar ve verified/version2 kalır. Concurrent username de kaybolabilir. Partial scope korunmalı, derived normalized yalnız username yazılınca eklenmeli; gerçek signal regression gerekli.
Sonuç: F gate failed, G başlamadı. Başka P1/P2 yok. Kaynak yazılmadı; testler bu race'i kapsamadığından geçti.
Yapılmayanlar: gerçek PostgreSQL concurrency, Redis/SMTP/browser/runtime/deploy not_verified.
