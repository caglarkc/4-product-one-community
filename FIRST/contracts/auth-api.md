# FIRST auth — ilk uygulama sözleşmesi

17 Eylül 2026. Ürün kaynağı: ../auth-kararlari.md. Kullanıcı tarafından onaylanmış başlangıç sözleşmesidir. Güncel normal auth ekleri aşağıdadır; A–E uygulandı, F–H kullanıcı talimatıyla bekliyor. Backend uzak sunucuda Docker içinde çalışacaktır; bu görevde yerel .venv ve izole kod/API testleri açıkça yetkilendirildi, dinleyen servis kurulmadı. Sonraki kabul edilmiş kurallar `../auth-kararlari.md` içindedir.

## Mimari

Django/DRF kimlik ve yetki kaynağı; django-allauth Google/GitHub OAuth işlemlerini yürütür. Tarayıcı HttpOnly Django session cookie + CSRF kullanır; bearer token localStorage'da tutulmaz. Next.js `/api/*` ve `/accounts/*` yollarını sabit `BACKEND_URL` adresine proxy eder. Tarayıcı aynı origin'i kullanır. Ortak dört ürün SSO'su bu ilk entegrasyonda kurulmaz. Kalıcı veritabanı PostgreSQL olacaktır. Auth işlemlerinde Redis kullanılacak; oturum/sayaç/geçici veri sorumlulukları uygulama öncesinde netleştirilecektir. E-posta SMTP üzerinden gönderilir.

Tüm JSON endpoint'leri `/api/auth/` altında, son slash zorunlu. Başarılı kullanıcı cevabı `{user: User}`; hata `{detail: string, errors?: Record<string,string[]>}`. Kullanıcı: `id, email, username, full_name, birth_date (ISO|null), gender ('female'|'male'|'other'|'unspecified'|''), phone (string), email_verified (bool), phone_verified (bool), profile_complete (bool), providers (string[]), capabilities: {can_apply: bool, can_create_listing: bool}`. `can_create_listing` yalnız hesap önkoşullarını gösterir; seçilen repo yetkisi ilan endpoint'inde ayrıca kontrol edilecektir.

| Metot/yol | Girdi | Sonuç |
|---|---|---|
| GET csrf/ | — | `{csrfToken: string}` + CSRF cookie |
| GET config/ | — | `{providers: {google: bool, github: bool}, phone_verification_available: false}` |
| GET me/ | — | `{user: User|null}` |
| POST register/ | email,password,username,full_name,birth_date,gender,phone? | 201 `{user}`; oturum açılır; doğrulama e-postası gönderilir |
| POST login/ | email,password | 200 `{user}` |
| POST logout/ | {} | 200 `{detail}`; session sona erer |
| PATCH profile/ | username,full_name,birth_date,gender,phone? | 200 `{user}`; sosyal kayıt zorunlu alanlarını tamamlar |
| POST email/resend/ | {} | 200 genel sonuç; authenticated |
| POST email/verify/ | key | 200 `{detail}`; kullanıcı sayfası yeniden me/ çeker |
| POST password/reset/ | email | 200 genel cevap; hesap varlığı açıklanmaz |
| POST password/reset/confirm/ | uid,token,password | 200 `{detail}` |
| POST password/change/ | old_password,password | 200 `{detail}`; authenticated |

Bütün mutation'lar anonim login/register dahil CSRF korumalıdır; backend parola kuralları, yaş ve benzersizlik kontrolünü uygular. Profil tamamlanmadan proje işlemi yetkisi yoktur. Güvenilir biçimde doğrulanmış sağlayıcı e-postası mevcut hesapla eşleşirse otomatik giriş ve sağlayıcı bağlama yapılır; ayrıca mevcut oturumdan connect akışı da korunur. Doğrulanmamış adresle mevcut hesaba erişim verilmez. Sağlayıcı kimliği başka hesaba bağlıysa sessizce taşınmaz. Önceden doğrulanmamış FIRST hesabı eşleştirilirken eski oturumlar kapatılır ve önceki yerel şifre yenilenmeden kullanılamaz. Google/GitHub bağlantısı kaldırma yoktur.

Sosyal başlangıç: native POST form `/accounts/google/login/` veya `/accounts/github/login/`, `csrfmiddlewaretoken`, `process=login|connect`, `next=/hesap`. Callback sağlayıcıda frontend origin + `/accounts/{provider}/login/callback/`. Başarı `/hesap`, sosyal hata `/giris?social_error=1`. Eksik profile sahip kullanıcı `/profil-tamamla` akışına yönlenir. Eksik/güvenilmez sağlayıcı e-postası doğrulanmış sayılmaz; kullanıcıdan e-posta alınır ve FIRST doğrulama bağlantısı gönderilir. Doğrulama gerektirmeyen alanlara erişilebilir; mevcut hesaba erişim ancak e-posta sahipliği doğrulandıktan sonra sağlanır. Sağlayıcı credentials yoksa seçenek kapalı ve açıklamalı görünür; sahte sosyal giriş yoktur.

E-posta linki frontend `/eposta-dogrula?key=...`; şifre sıfırlama linki `/sifre-sifirla?uid=...&token=...`. Linkleri açmak tek başına mutation yapmaz, kullanıcı form gönderir.

Telefon kayıt/profilde isteğe bağlı ve uluslararası formatta normalize edilir; doğrulanmış numara tek hesaba aittir; doğrulanmamış giriş gerçek sahibin doğrulamasını engellemez. Sağlayıcı seçilene kadar `phone_verified=false`; telefonun varlığı doğrulama değildir. UI doğrulanmış gibi göstermez ve ilan önkoşulu kapalı kalır. Gerçek SMS/WhatsApp ve repo yetki entegrasyonu takip işleridir.

## Onaylanan ek kurallar ve tamamlanacak endpoint sözleşmeleri

- Şifre: 8–20 karakter, boşluksuz; büyük/küçük harf, sayı ve özel karakter zorunlu. Türkçe karakter kabul edilir; yaygın/ele geçirilmiş şifreler reddedilir.
- Kullanıcı adı: 3–30 karakter, harf/rakam/alt çizgi; büyük/küçük harften bağımsız benzersiz.
- E-posta doğrulama: 24 saat; yeniden gönderim 60 saniye arayla, adres başına en fazla 5/saat.
- Şifre sıfırlama: 30 dakika, tek kullanım; başarıda bütün oturumlar kapatılır ve yeniden giriş gerekir.
- Oturum: normal 24 saat, beni hatırla 30 gün. Login girdisine beni hatırla seçimi eklenecektir; kesin alan sözleşmesi henüz tanımlanmadı.
- Hassas hesap değişiklikleri: son 10 dakika içinde yeniden doğrulama.
- Hesap başına 15 dakikada 5 başarısız şifre denemesi sonrası geçici bekleme; ayrıca IP sınırı. IP eşiği ve bekleme süresi henüz belirlenmedi.
- Oturum listeleme/tekil veya toplu kapatma, yeniden doğrulama, e-posta değiştirme ve sosyal kullanıcıya şifre oluşturma endpoint'leri uygulama öncesinde tanımlanacaktır. Mevcut tablo bu yeni akışları henüz kapsamaz.
- E-posta değişiminde eski adres yeni adres doğrulanana kadar geçerlidir; eski adrese bildirim gider. Başka hesaba ait adresle değişiklik, hesap birleştirme yapmaz.
- Google/GitHub bağlantısı kaldırma endpoint'i olmayacaktır.

## Normal auth uygulama sözleşmesi — bu görevde geçerli ek

OAuth/connect ve sosyal UI bu teslimin dışındadır; config iki sağlayıcı için de false döner. Gelecekte django-allauth bağlanabilir; provider kimliği kullanıcı modelindeki e-postaya gömülmez. Aşağıdaki alanlar önceki tabloda belirsiz alanları kesinleştirir:

| Metot/yol | Girdi | Sonuç |
|---|---|---|
| POST register/ | Yukarıdaki alanlar | 201 `{user}`; SMTP hatası 503 `{detail, code: 'email_delivery_failed'}`; hesap/oturum başarı olarak sunulmaz |
| POST login/ | email,password,remember_me (boolean, varsayılan false) | 200 `{user}`; geçersiz kimlik 400 genel hata; limit 429 |
| POST reauthenticate/ | password | 200 `{detail}`; mevcut oturumda 10 dakika yetki |
| POST email/change/ | email | authenticated + yakın yeniden doğrulama; 200 `{detail}`; eski adres korunur, yeni adres doğrulama bağlantısı ve eski adrese bildirim |
| GET sessions/ | — | `{sessions: [{id, created_at, expires_at, current}]}`; opaque id; ham session key/IP yok |
| DELETE sessions/{id}/ | — | 200 `{detail}`; sadece kendi oturumu; yabancı/yok 404 |
| POST sessions/revoke/ | {} | 200 `{detail}`; mevcut dahil bütün oturumları kapatır; yakın yeniden doğrulama |
| POST password/change/ | old_password,password | authenticated + yakın yeniden doğrulama; başarı bütün oturumları kapatır |

Korumalı isteklerde oturum yoksa 401; CSRF hatası 403 `{detail, code:'csrf_failed'}`. Yakın yeniden doğrulama eksikse 403 `{detail, code:'reauthentication_required'}`. Doğrulama hataları 400 `{detail,errors}`; token yok/geçersiz/eskimiş/kullanılmış 400 `{detail,code:'invalid_token'}`. Rate limit 429; Redis/SMTP kullanılamadığında 503; iç servis hata ayrıntısı ve secret sızdırılmaz. Tüm yanıtlar `Cache-Control: no-store` taşır. Bilinmeyen mutation alanları reddedilir.

Profil PATCH yalnız username/full_name/birth_date/gender/phone kabul eder; e-posta/verified/capabilities/providera yazılamaz. Telefon uluslararası `+` ve 8–15 rakam biçimine normalize edilir; doğrulanmış sayılmaz. Kullanıcı adı Unicode harf/rakam/alt çizgi, NFC + casefold benzersizlik; e-posta trim + lower ile normalize edilir. Tarih sunucuda gün bazında 13. doğum gününü tamamlamalıdır. Alan uzunlukları: full_name 150, email 254, phone 32 girdi karakteri. Kayıt ve profil cinsiyeti female/male/other/unspecified olmalıdır.

POST email/verify/ hem kayıt hem değişiklik bağlantısını onaylar. E-posta değişiklik token'ı kullanıcı ve mevcut eski adrese bağlıdır; yeni istek önceki bekleyen değişikliği geçersiz kılar; doğrulamada yeni adresin benzersizliği tekrar kontrol edilir, hesap birleştirilmez. Değişiklik onayında oturumlar kapatılır. GET bağlantı açılışı sadece formu gösterir.

POST password/reset/ her hesap durumu için aynı genel cevap; SMTP kesintisinde hesap varlığı açıklanmaması için gönderim sonucu cevap biçimini değiştirmez ve operasyonel hata kaydı tutulur. Sıfırlama token'ı 30 dakika/tek kullanım; yalnız sahipliği e-posta ile kanıtlayan kullanıcı yerel şifre oluşturabilir. Yanıtta uid/token bulunmaz. Linkler yalnız yapılandırılmış frontend origin'inden üretilir; Host başlığı kullanılmaz.

Test sınırı: süreç içi Django client `enforce_csrf_checks=True`, izole SQLite, Redis test double ve locmem mail; web bileşen/sözleşme/lint/typecheck/build. Gerçek PostgreSQL, Redis atomiklik/TTL/arıza, SMTP teslim, tarayıcı E2E, sunucu ve deploy `not_verified`.

Limit ayrıntısı: login, reauthenticate ve old_password denetimi aynı hesap-başına başarısız şifre sayacını paylaşır (5/15 dakika); IP başına tüm şifre kanıtı denemeleri 30/15 dakika. Reset isteği normalize adres başına 5/saat, IP başına 30/15 dakika; sayaç bilinmeyen adresler için de aynı şekilde işler, limitte aynı 429 hata döner. E-posta varlığı, doğrulanma durumu veya SMTP sonucu bu yanıtları ayırt ettirmez. E-posta yeniden gönderimde mevcut adres başına 60 saniye aralık ve saatte en fazla 5 gönderim kuralı korunur.

Proxy istemci IP sözleşmesi: varsayılan backend REMOTE_ADDR; production per-client mode için server-only AUTH_PROXY_SECRET (iki tarafta aynı, en az32 karakter) ve frontend AUTH_CLIENT_IP_HEADER yapılandırılır. Header yalnız trusted ingress tarafından overwrite edilmelidir; gerçek ortam doğrulaması ayrı. Next canonical tek IP'yi `ip\nseconds\nMETHOD\n/api/auth/path/` üzerinde HMAC-SHA256 imzalar; X-First-Client-IP/Time/Signature. Secret aktif backend tüm auth isteklerinde geçerli ±60s assertion ister (403 invalid_proxy_assertion); secret yokken kullanıcı assertion başlıkları yok sayılır. Hiçbir key/credential browser bundle'a girmez.

### E teslimindeki uygulanan kapsam

Yalnız csrf/config/register/login/me/logout endpoint’leri aktiftir. Bu sözleşmedeki hesap yönetimi endpoint’leri F/G için tanımlıdır, henüz uygulanmadı. Web `/giris`, `/kayit`, geçici `/hesap` ve aynı-origin auth proxy içerir. E bağımsız kapıları geçti; kullanıcı F öncesinde bekleme istedi. Önceki paragraflardaki gelecekte tamamlanacak alan notlarını normal auth eki kesinleştirir.
