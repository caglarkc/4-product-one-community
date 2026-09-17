# F revision bağımsız verification — contract_audit — PASS
Görev/dosyalar: f-verify-r2; backend User.save ve tüm auth testleri.
Komutlar FIRST/backend: .venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity1 —65 passed1.025s; check clean; makemigrations --check --dry-run no changes. Ek .venv/bin/python stdin probe1test0.136s passed.
Probe gerçek email-change/verify API ile yeni adres doğruladı, eski instance ile gerçek user_logged_in signal gönderdi; yeni email/verified/version korundu, last_login güncellendi. Önceki P1 giderildi. Partial scope ve3 regressions geçti.
Yapılmayanlar: gerçek PostgreSQL yarışları/Redis/SMTP/browser/runtime/deploy not_verified; kullanıcı sınırı. Kaynak yazılmadı, servis başlamadı.
