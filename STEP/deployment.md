# STEP — Kurulum ve dağıtım

STEP kendi PostgreSQL verisi, backend, web ve worker servisleriyle çalışır. FIRST sunucusuna bu görevde dağıtım yapılmadı. Kaynaklar incelendi; aşağıdaki kurulum/build/migration/runtime komutları kullanıcı tercihi gereği bu teslimde çalıştırılmadı.

## Yerel ilk test

Docker Engine + Compose v2 ve Python 3 gereklidir. Proje kökünden:

```sh
python3 STEP/deploy/configure.py
cd STEP
docker compose build
docker compose up -d db
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py step_operator --email operator@example.org --name Operator
docker compose up -d backend worker web
```

Operatör e-postasını gerçek hesabınızla değiştirin; şifre terminalde gizli istenir. İlk altı gerçek kategori oluşturulur, sahte ilan/kullanıcı eklenmez. Web `http://localhost:3001`, API `http://localhost:8002/api/v1/`; aynı hostname kullanın. `127.0.0.1` ile `localhost` karıştırılırsa çerezler paylaşılmaz. Yönetim ekranında kredi politikası, takip hareketsizlik/önizleme değerleri ve çekim koşulları ayarlanır. Kararı ertelenen ticari rakamlar otomatik doldurulmaz; ilgili akış eksik ayarı bildirir. Test kredi dağıtımı operatörden yapılır.

Gerçek `STEP/.env` bu görevde yerelde oluşturuldu; `configure.py` mevcut anahtarları korur. `STEP_PAYMENT_PROVIDER=simulator`, test + DEBUG şartıyla açık bir yerel para fixture'ıdır. Kredi ve iş fonlama senaryosu gerçek PSP sandbox kanıtı değildir. Test kayıtları canlı veritabanına taşınmaz; canlı için farklı veritabanı ve ayrı provider yapılandırması gerekir.

Yerel frontend Docker dışında geliştirilecekse `STEP/frontend/.env.local` içindeki gerçek API adresi kullanılır; Node 22 gerekir. Bu env yalnız public API adresini taşır. Sonradan hedef adresi değişirse frontend build-time env ile yeniden build edilmelidir.

## E-posta, sağlayıcı ve doğrulama

SMTP host/user/password/from ve web URL gerçek `.env` içinde ayarlanır; eksik SMTP ile sıfırlama/öğrenci doğrulama gönderimi başarılı gösterilmez. Üniversite öğrenci alan adlarını yönetimden gerçek kanıtla ekleyin. Test girişinde öğrenci/işveren doğrulaması ertelenir; canlı başvuru/yayın için backend uygunluk kapıları zorunludur.

Gerçek iyzico sandbox için `STEP_PAYMENT_PROVIDER=iyzico_sandbox`, sandbox anahtarları, sağlayıcının erişebildiği HTTPS `STEP_API_URL`, callback ve seller onboarding gerekir. Gerçek para ancak retrieve yanıtının durum/tutar/para birimi/hedef doğrulamasıyla fonlanmış sayılır. Marketplace bekletme, kısmi serbest bırakma/iade, rollover ve banka settlement kabiliyetleri sağlayıcının bu işletmeye verdiği izinlerle doğrulanmalıdır. Hesap/anahtar olmadan adapter kaynakları canlı entegrasyon kanıtı değildir. Netgsm OTP değerleri de gerçek hesabın anahtarlarını gerektirir. [Sağlayıcı sözleşmesi](contracts/providers.md) sınırları uygulanır.

Canlıya geçiş ayrı release işlemidir: `STEP_MODE=live`, DEBUG kapalı, iyzico_live anahtarları, onaylı sayısal politika, üniversite listesi, SMTP/OTP/kimlik ve şirket kanıt süreci, provider kabiliyetleri, imzalı tracker dağıtımı ve işletme operasyonları tamamlanır. Readiness eksiklerini yönetim ekranı gösterir. Test volume/env yerinde mode değiştirerek canlıya dönüştürülmez.

## HTTPS ve işletim

Compose dosyası loopback yerel başlangıç içindir; public internete doğrudan debug portu açmayın. Canlı reverse proxy yalnız HTTPS sunmalı, web/API aynı site altında yapılandırılmalıdır. Ayrı siteler seçilirse `STEP_COOKIE_SAMESITE=None` yalnız HTTPS/Secure ile ve exact `STEP_WEB_ORIGINS` izin listesiyle kullanılır. Origin `*` verilmez. Proxy request scheme/IP yalnız güvenilen proxy üzerinden yapılandırılır; rastgele forwarded header'a güvenilmez.

Veritabanı (`step-postgres`) ve private dosyalar (`step-private`) kalıcı, birbirine bağlı yedeklenir; geri dönüş migration uyumluluğu ve provider kayıtlarıyla değerlendirilir. `docker compose down` volume silmez; `down -v` veriyi siler. Worker DB lease ve outbox ile zamanlı süreçleri yürütür; unknown provider işlemi kör yeniden gönderilmez. Operatör kuyruk/uzlaştırma üzerinden ele alır. Ekran görüntüleri static/public URL ile servis edilmez; bütün erişim authenticated API'den geçer.

## Masaüstü

[STEP tracker kurulumu](desktop/README.md) Windows/macOS/Linux kaynak ve paketleme adımlarını içerir. Her OS native bağımlılık ve izin gerektirir. macOS screen recording/input monitoring/accessibility, Windows masaüstü oturumu, Linux X11 gereklilikleri kurulumda belirtilir; Wayland bu kaynak sürümünde kapalıdır. İmzalı/notarized native paketler bu görevde üretilmedi veya çalıştırılmadı. API device token yalnız tracker scope'lu, süreli ve iptal edilebilir; sistem keyring ve AES-GCM offline queue kullanılır.

## Yapılmamış doğrulamalar

Test, lint, typecheck, Docker/Next/native build, migration uygulama, tarayıcı, ekran kaydı, sağlayıcı/SMTP/OTP canlı çağrısı bu teslimin kontrol kapsamına alınmadı. Kurulum komutları hazır kaynak iş akışıdır; başarılı runtime/deploy raporu değildir.

Resmî dayanaklar: [Docker Compose env](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/), [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [Next.js deployment](https://nextjs.org/docs/app/getting-started/deploying).
