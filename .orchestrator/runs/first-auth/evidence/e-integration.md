# E backend/web integration
Görev/dosyalar: e-integration; frontend backend-proxy.ts/api.ts/auth-form.tsx/route handler/tests, backend proxy.py/views.py/serializers/urls/settings, auth-api.md.
Komut: source cat/rg; node /tmp/first-proxy-bridge.mjs; FIRST/backend/.venv/bin/python stdin integration probe (script agent tool kaydında).
Sonuç: gerçek Node proxyAuth fonksiyonu mock upstream ile IPv4 ve expanded IPv6 assertion üretti; gerçek Python TrustedClientIPMiddleware ikisini kabul etti, değiştirilmiş path ikisinde403. 4 çapraz dil kontrolü geçti; ağ/database/listener yok. Script/fixtures /tmp içinde sentetik veridir ve Git'e alınmaz. Headers/code/body/UI ve trailing slash mapping kaynakları önceki E review/test ile eşleşir. İlk proxy_ip.py okuma denemesi yanlış dosya adı nedeniyle başarısız, rg ile gerçek proxy.py bulundu ve okundu.
Bağımsız E revision review ve verification tamamlanınca graph kabulü yapılır; belge tek başına pass değildir.
Yapılmayanlar: gerçek HTTPS/ingress/proxy client IP/cookies/browser, PostgreSQL/Redis/SMTP/deploy not_verified. Kullanıcı sınırı.
