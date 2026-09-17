# FIRST auth — ilk uygulama sözleşmesi

17 Eylül 2026. Ürün kaynağı: ../auth-kararlari.md. Bu sözleşme ilk yerel entegrasyon içindir; canlı servis kurulumu değildir.

## Mimari

Django/DRF kimlik ve yetki kaynağı; django-allauth Google/GitHub OAuth işlemlerini yürütür. Tarayıcı HttpOnly Django session cookie + CSRF kullanır; bearer token localStorage'da tutulmaz. Next.js `/api/*` ve `/accounts/*` yollarını sabit `BACKEND_URL` adresine proxy eder. Tarayıcı aynı origin'i kullanır. Ortak dört ürün SSO'su bu ilk entegrasyonda kurulmaz. SQLite yalnız yerel geliştirme/test içindir; üretim DB seçimi değildir.

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

Bütün mutation'lar anonim login/register dahil CSRF korumalıdır; backend parola kuralları, yaş ve benzersizlik kontrolünü uygular. Profil tamamlanmadan proje işlemi yetkisi yoktur. E-posta eşleşmesi hesapları otomatik birleştirmez. Sosyal hesap bağlama mevcut oturumda explicit connect işlemidir.

Sosyal başlangıç: native POST form `/accounts/google/login/` veya `/accounts/github/login/`, `csrfmiddlewaretoken`, `process=login|connect`, `next=/hesap`. Callback sağlayıcıda frontend origin + `/accounts/{provider}/login/callback/`. Başarı `/hesap`, sosyal hata `/giris?social_error=1`. Eksik profile sahip kullanıcı `/profil-tamamla` akışına yönlenir. Eksik/güvenilmez sağlayıcı e-postası doğrulanmış sayılmaz; kullanıcıdan e-posta almak için backend ve frontend uyumlu hata/complete akışı sağlanmalıdır. Sağlayıcı credentials yoksa seçenek kapalı ve açıklamalı görünür; sahte sosyal giriş yoktur.

E-posta linki frontend `/eposta-dogrula?key=...`; şifre sıfırlama linki `/sifre-sifirla?uid=...&token=...`. Linkleri açmak tek başına mutation yapmaz, kullanıcı form gönderir.

Telefon kayıt/profilde isteğe bağlı ve uluslararası formatta normalize edilir; tek hesaba aittir. Sağlayıcı seçilene kadar `phone_verified=false`; telefonun varlığı doğrulama değildir. UI doğrulanmış gibi göstermez ve ilan önkoşulu kapalı kalır. Gerçek SMS/WhatsApp ve repo yetki entegrasyonu takip işleridir.
