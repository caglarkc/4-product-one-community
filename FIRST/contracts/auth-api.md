# FIRST auth — ilk uygulama sözleşmesi

17 Eylül 2026. Ürün kaynağı: ../auth-kararlari.md. Kullanıcı tarafından onaylanmış başlangıç sözleşmesidir; henüz uygulanmadı. Backend uzak sunucuda Docker içinde çalışacaktır; geliştirici bilgisayarında backend kurulumu yapılmaz. Sonraki kabul edilmiş kurallar `../auth-kararlari.md` içindedir.

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
