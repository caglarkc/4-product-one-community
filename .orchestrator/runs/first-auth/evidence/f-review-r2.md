# F revision bağımsız review — backend_review — PASS
Görev/dosyalar: f-review-r2; accounts/models.py ve3 yeni test_account regression.
Komut FIRST/backend: .venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity1 —65 passed1.071s; system check temiz. Source/test okuma.
Sonuç: update_fields korunuyor; email yalnız yazıldığında normalize, username_normalized yalnız username yazıldığında derived. Actual update_last_login(None,stale_user) yeni email/verified/version/username değerlerini koruyor. Önceki P1 giderildi; başka P1/P2 yok.
Yapılmayanlar: PostgreSQL concurrency ve gerçek Redis/SMTP/browser/runtime/deploy not_verified. Kaynak yazılmadı/servis başlamadı.
