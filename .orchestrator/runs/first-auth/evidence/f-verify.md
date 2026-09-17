# F bağımsız verification — contract_audit — PASS (review ayrı failed)
Görev/dosyalar: f-verify; backend account source/tests/migrations.
Komutlar FIRST/backend: .venv/bin/python manage.py test accounts --settings=config.test_settings --verbosity1 —62passed0.945s; check clean; makemigrations --check --dry-run no changes. .venv/bin/python stdin bağımsız probe6checks0.227s passed.
Ek kontroller: DELETE CSRF403 nonmutating; wrong UID doesn't consume then correct UID passes; verify token cannot reset; email-change revokes2sessions; changing verified phone resetsfalse; future reauth doesn't authorize.
Sonuç: suite ve probes geçti, kaynak değişmedi. Ayrı review P1 partial-save race buldu; revision sonrası gate yeniden kontrol edilir.
Yapılmayanlar: gerçek PostgreSQL locking, Redis Lua/TTL/outage, SMTP delivery, token-consume/DB-rollback distributed faults, browser/runtime/deploy not_verified; kullanıcı sınırı.
