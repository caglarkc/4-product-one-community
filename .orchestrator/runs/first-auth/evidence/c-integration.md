# C backend → web geçiş kontrolü
Görev/dosyalar: c-integration; FIRST/backend/accounts/urls.py, views.py, serializers.py, authentication.py, middleware.py, config/settings.py; FIRST/contracts/auth-api.md.
Komut: cat yukarıdaki gerçek kaynaklar; rg route/serializer/session ayarları; graph validate.
Kaynak karşılaştırması: /api/auth/{csrf,config,me,register,login,logout}/ trailing slash; csrfToken JSON, HttpOnly session cookie, login remember_me boolean, me user/null; register 201; field error400/errors; yanlış login genel400; CSRF403/code; rate429; SMTP/Redis503. User allowlist sözleşmeye uygun, provider false; profil/repo capability false. Doğrulanmamış giriş açık. Frontend sonraki aşamada gerçek relative API fetch ve her mutation öncesi taze CSRF kullanmalı (login token rotation var).
Proxy koşulu: sabit server-only BACKEND_URL; tarayıcı same-origin /api/auth; frontend origin CSRF_TRUSTED_ORIGINS içinde; HTTPS secure cookie için zorunlu. Tarayıcı/proxy çalışma zamanı bu kaynak kontrolüyle kanıtlanmış sayılmaz.
Kontrol sonucu: bağımsız C revision review/verification tamamlandıktan sonra graph record ile kabul edilecek. Bu belge tek başına kapı başarısı değildir.
Yapılmayanlar: dinleyen servis, PostgreSQL/Redis/SMTP gerçek entegrasyonu, tarayıcı E2E/proxy/cookie/runtime/deploy kullanıcı kapsam dışı ve not_verified.
