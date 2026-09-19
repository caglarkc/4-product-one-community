# FIRST auth API sözleşmesi

17 Eylül 2026. Ürün kararları: [auth-kararlari.md](../auth-kararlari.md). Bu belge normal auth ve aşağıdaki sağlayıcı genişletmelerini tanımlar. Ortak ürün SSO’su, ilan/repo ve öğrenci doğrulama kapsam dışıdır. Bağlantı kaldırma ekranı veya endpoint’i yoktur.

## Taşıma ve kimlik

Django + DRF yetki kaynağıdır. Web/mobil doğrudan `https://167.235.158.118/api/auth/` adresini çağırır; Vercel API proxy ve HMAC katmanı yoktur. `Authorization: Bearer <opaque-session>` Redis/Django oturumunu taşır. Web `credentials: omit` kullanır, anahtarı localStorage içinde saklar. Backend yeni/dönen/silinen anahtarı `X-First-Session` başlığında iletir; boş değer temizleme anlamındadır. Geçersiz/süresi dolan anahtar 401 `invalid_session`; cookie fallback yoktur. Anonim `csrf/` oturumu sabit 10 dakika ve IP sınırlamalıdır. Bütün mutation'lar session-bound `X-CSRFToken` gerektirir. Native istemci aynı bootstrap ve yapılandırılmış FIRST Origin başlığını kullanır. Son slash zorunlu, yanıtlar no-store. Eski cookie kullanıcıları yeniden giriş yapar.

Production kalıcı veri PostgreSQL'de kullanıcı ve oturum iptal kayıtlarıdır. Redis oturum içeriğini, deneme sayaçlarını ve anahtarı hash'lenmiş süreli token'ları tutar; process-local production fallback yoktur. Normal oturum 24 saat, `remember_me=true` 30 gün; süre mutlak, etkinlikle uzamaz. Her istek kalıcı oturum kaydı, süre ve kullanıcı güvenlik sürümünü kontrol eder. Doğrulanmamış e-postayla giriş serbesttir; web hatırlatma gösterir.

## Yanıt ve alanlar

Kullanıcı yanıtı `{user: User}`; `me/` anonim durumda `{user:null}` döner. `User`:

```text
id: number; email, username, full_name, phone: string
birth_date: ISO date | null
gender: female | male | other | unspecified | ''
email_verified, phone_verified, profile_complete: boolean
providers: (google | github)[]
has_usable_password: boolean
capabilities: {can_apply:false, can_create_listing:false}
```

İlan/başvuru henüz uygulanmadığından capabilities false'dur; gelecekteki yetki garantisi değildir. Şifre hash'i, session key, token, security_version ve iç servis bilgileri kullanıcı yanıtına girmez.

Hata biçimi `{detail:string, errors?:Record<string,string[]>, code?:string}`. Alan doğrulaması ve yanlış şifre 400; korumalı oturumsuz istek 401; CSRF 403 `csrf_failed`; son 10 dakikada şifre kanıtı eksikse 403 `reauthentication_required`; geçersiz/eski/kullanılmış token 400 `invalid_token`; yabancı/yok oturum 404; limit 429; Redis/SMTP servis sorunu 503. Reset isteği SMTP istisnası aşağıdadır. Bilinmeyen mutation alanları reddedilir. İç hata ayrıntıları ve secret gönderilmez.

## Endpoint'ler

Tüm yollar `/api/auth/` altındadır. JSON nesnesi gönderilir; boş mutation `{}`. “Yakın kanıt”, mevcut oturumda son 10 dakika içinde şifreyle yeniden doğrulamadır.

| Metot / yol | Girdi | Başarı ve yetki |
|---|---|---|
| GET csrf/ | — | 200 `{csrfToken}` + gerektiğinde `X-First-Session`; anonim |
| GET config/ | — | 200 `{providers:{google:false,github:false},phone_verification_available:false}` |
| GET me/ | — | 200 `{user:User|null}` |
| POST register/ | email,password,username,full_name,birth_date,gender,phone? | 201 `{user}`; oturum açar, doğrulama e-postası gönderir |
| POST login/ | email,password,remember_me?:boolean=false | 200 `{user}`; yanlış kimlik için genel hata |
| POST logout/ | {} | 200 `{detail}`; mevcut oturumu kapatır |
| PATCH profile/ | username?,full_name?,birth_date?,gender?,phone? | 200 `{user}`; oturum gerekli |
| POST reauthenticate/ | password | 200 `{detail}`; mevcut oturum için yakın kanıt |
| POST password/reset/ | email | 200 genel `{detail}`; anonim, hesap varlığı açıklanmaz |
| POST password/reset/confirm/ | uid,token,password | 200 `{detail}`; anonim, bütün oturumları kapatır |
| POST password/change/ | old_password,password | 200 `{detail}`; oturum + yakın kanıt; bütün oturumları kapatır |
| POST email/resend/ | {} | 200 `{detail}`; oturum gerekli |
| POST email/verify/ | key | 200 `{detail}`; anonim token kanıtı, kayıt veya adres değişikliği onayı |
| POST email/change/ | email | 200 `{detail}`; oturum + yakın kanıt; eski adres değişmez |
| GET sessions/ | — | 200 `{sessions:[{id,created_at,expires_at,current}]}`; yalnız kendi aktif oturumları |
| DELETE sessions/{uuid}/ | {} | 200 `{detail}`; yalnız kendi oturumu; mevcut oturum seçilirse çıkış |
| POST sessions/revoke/ | {} | 200 `{detail}`; oturum + yakın kanıt; mevcut dahil bütün oturumları kapatır |

## Doğrulama ve güvenlik kuralları

- Şifre 8–20 Unicode codepoint; boşluk yok; büyük/küçük harf, sayı ve özel karakter zorunlu. Türkçe karakter kabul edilir. Yaygın şifreler Django listesi ve yerel küçük denylist ile reddedilir; ek offline ihlal corpus'u `AUTH_BREACHED_PASSWORD_FILE` ile sağlanabilir. Geniş ihlal corpus kapsamı bu teslimde doğrulanmadı; ayrıntı [backend README](../backend/README.md).
- Kayıtta ad soyad, kullanıcı adı, e-posta, şifre, doğum tarihi ve cinsiyet zorunlu; telefon isteğe bağlı. En az 13 yaş gün bazında hesaplanır. full_name en fazla150, email254, phone girdi32 karakterdir.
- Kullanıcı adı NFC sonrası3–30 Unicode harf/rakam/alt çizgi; NFC+casefold benzersiz. E-posta trim+lower normalize edilir, benzersizdir. Cinsiyet female/male/other/unspecified olmalıdır.
- Profil PATCH yalnız tabloda sayılan profil alanlarını kabul eder; email/verified/provider/capabilities yazılamaz. Telefon boşaltılabilir veya uluslararası `+` ve8–15 rakama normalize edilir. Ekleme/değiştirme her zaman `phone_verified=false` bırakır.
- Login, reauthenticate ve old_password ortak hesap sayacını kullanır:5 başarısız deneme/15dakika; IP başına30 şifre kanıtı/15dakika. Başarılı kanıt hesap sayacını temizler. Hash öncesi Redis rezervasyonu ve30s kilit vardır; eşzamanlı kanıt429 alabilir.
- Reset isteği normalize adres başına5/saat ve IP30/15dakika; bilinmeyen adres de aynı bütçeyi tüketir. Bilinen/bilinmeyen/pasif hesap ve SMTP hatası aynı200 yanıtı verir; mail arızası güvenli operasyonel log'a yazılır. Senkron SMTP nedeniyle zamanlama üzerinden hesap varlığını gizleme garantisi yoktur.
- Doğrulama bağlantısı24saat; adres başına60s aralık ve5/saat bütçe ilk kayıt dahil paylaşılır. Başarısız SMTP denemesi de rezervasyonu tüketir. Kayıt gönderim hatası503 `email_delivery_failed`; hesap/oturum sahte başarı olarak sunulmaz.
- Reset token'ı30dakika ve tek kullanımdır; kullanıcı/e-posta/güvenlik sürümüne bağlıdır. Linkte uid ondalık kullanıcı kimliğidir. Yeni şifre token tüketilmeden doğrulanır. Başarı kalıcı güvenlik sürümünü artırır ve bütün oturumları iptal eder; yeniden giriş gerekir.
- E-posta değişimi yeni adrese doğrulama, eski adrese bildirim gönderir. Yeni adres onaylanana kadar eski adres geçerlidir. Başarıyla üretilen sonraki değişiklik isteği önceki bekleyen değişikliği geçersiz kılar. Onayda adres benzersizliği tekrar kontrol edilir; hesap birleştirilmez. Onay bütün oturumları kapatır; eski kayıt token'ı yeni adresi doğrulayamaz.
- Hassas mutation'lar kullanıcı satırı kilidi altında taze güvenlik sürümü/oturum kaydını tekrar kontrol eder. Redis token tüketimi ile SQL tek dağıtık transaction değildir: tüketim sonrası SQL hatasında yeni bağlantı gerekir. SMTP dış etkisi geri alınamaz; kısmi adres-değişim gönderim hatası503 verir ve yeni token geçersiz kılınır. Gönderilmiş mesaj geri çağrılamaz.

## Web ve ortam

Web rotaları `/`, `/giris`, `/kayit`, `/hesap`, `/sifremi-unuttum`, `/sifre-sifirla?uid=…&token=…`, `/eposta-dogrula?key=…`. Ana sayfa yalnız temel gezinme ve oturum durumunu içerir; profil işlevseldir. Kayıt/giriş ana sayfaya; çıkış, şifre değişimi/reset ve mevcut/toplu oturum kapatma girişe yönlenir. E-posta doğrulama linkini GET ile açmak veri değiştirmez; kullanıcı onay formu gönderir. Doğrulamadan sonra web `me/` sorgular; adres değişimi nedeniyle kapanmış oturumu gösterir. Linkler yalnız `FRONTEND_ORIGIN` üzerinden üretilir, Host başlığına güvenilmez.

Exact-origin CORS yalnız yapılandırılmış frontend/local origin değerlerine izin verir; Authorization, Content-Type ve X-CSRFToken kabul edilir, X-First-Session açığa çıkarılır. nginx X-Real-IP ve HTTPS bilgisini overwrite eder; Docker portu loopback'e bağlıdır. `TRUST_NGINX_PROXY=true` yalnız bu korunan upstream'de kullanılır. Kimlik/sağlayıcı sırları backend'de kalır. IP TLS sertifikasının yenilenmesi korunur.

## Test sınırı

Django süreç içi client, `enforce_csrf_checks=True`, izole SQLite, FakeRedis ve locmem mail; frontend bileşen/sözleşme/lint/typecheck/build kullanılır. Mock'lar yalnız testtedir. Gerçek PostgreSQL kilit/eşzamanlılık, Redis Lua/TTL/arıza, SMTP teslim/zamanlama, proxy-ingress/HTTPS-cookie, tarayıcı E2E/görsel kullanım, Docker/uzak servis/deploy **not_verified**. Kod testlerinin geçmesi canlı ortamın çalıştığı anlamına gelmez. Kanıt ve korunmuş başarısız denemeler: [run checklist](../../.orchestrator/runs/first-auth/checklist.md).

- E-posta değiştirme: hedef adresten bağımsız kullanıcı başına 60 saniye aralık ve 5/saat, istemci IP başına 30/15 dakika. Redis bu üç bütçeyi atomik ayırır; hedef adres bütçesi ayrıca uygulanır. Hedef/SMTP başarısızlığı rezervasyonu geri almaz.

## Google giriş/kayıt genişletmesi — 18 Eylül 2026

Bu bölüm Google akışını tanımlar; GitHub genişletmesi ayrı bölümde açıklanır.
Google yalnız giriş, kayıt ve bağlı kimlikle yeniden doğrulama içindir. Uygulama içinden
Google bağlama/kaldırma endpoint'i yoktur. `django-allauth` Google kimlik doğrulama ve
kalıcı sağlayıcı kimliği için kullanılır; FIRST oturum kayıtları yetki kaynağı kalır.

| Metot / yol | Girdi | Sonuç |
|---|---|---|
| POST google/start/ | remember_me?:boolean, purpose?:login veya reauth | CSRF korumalı; `{authorization_url}` |
| GET google/callback/ | code,state veya error,state | Oturuma bağlı tek kullanımlı state; `{status:authenticated veya profile_required veya reauthenticated,user?}` |
| GET google/signup/ | — | Süreli bekleyen kayıt; `{profile:{email,full_name,username,birth_date,gender,phone},email_verified,email_editable}` |
| POST google/signup/ | full_name,username,birth_date,gender,phone?,email? | CSRF; yerel şifre kabul edilmez; 201 `{user}` |

Google callback frontend yolu `/accounts/google/login/callback/` olarak sabittir.
Statik istemci callback sayfası izin verilen sorgu alanlarını doğrudan backend JSON endpoint'ine Bearer ile taşır; adres çubuğunu temizler. Backend `redirect_to` döndürür, istemci yalnız sabit FIRST yollarını kabul eder. Başarılı mevcut giriş `/`, yeni kullanıcı
`/kayit/google`, başarılı yeniden doğrulama `/hesap` yönüne gider.

Sağlayıcıdan dönen token tarayıcıya verilmez. Google state, nonce ve PKCE kullanılır;
kimlik token imzası, issuer, audience ve süre denetlenir. Google subject kalıcı
kimliktir; e-posta daha sonraki girişlerde bağlı kimliği başka hesaba taşımaz.
Yalnız Google'ın adres sahipliğine güvenilir kanıt sağladığı e-posta otomatik eşleşir.
Gmail veya doğrulanmış Workspace haricindeki Google hesabında sırf email_verified
iddiası mevcut FIRST hesabına erişim sağlamaz.

Yeni kayıt için Google bilgileri öneri olarak doldurulur. Zorunlu profil ve en az 13
yaş koşulu sağlanmadan kullanıcı oluşturulmaz. Güvenilir e-posta değiştirilemez;
eksik/güvenilmeyen adres için önce FIRST e-posta doğrulama akışı kullanılır.
Adres ispatı tamamlanmadan sosyal kimlik veya nihai kullanıcı oluşturulmaz; mevcut
adres yalnız aynı bekleyen akışta mailbox kanıtıyla eşleştirilir. Hata sonrası form bilgileri korunur.

`config/` Google hazırsa `providers.google=true` döner. User yanıtında `providers`
bağlı sağlayıcıları ve `has_usable_password` kullanılabilir yerel şifre durumunu
bildirir. Sosyal kullanıcı için zorunlu şifre alanı gösterilmez; isterse mevcut şifre
sıfırlama akışıyla yerel şifre oluşturabilir. Hassas işlem Google yeniden doğrulamasında
aynı oturum ve zaten bağlı aynı Google kimliği gerekir; başka hesaba bağlama yapılmaz.

Güvenilir Google e-postası alınamayan bekleyen kayıt için ek POST uçları:
`google/email/request/` `{email}` ile FIRST doğrulama bağlantısı ister;
`google/email/verify/` `{key}` ile aynı bekleyen tarayıcı oturumunda açıkça onaylar.
Link `/google-eposta-dogrula?key=…` ekranını açar; GET tek başına onaylamaz.
Mevcut hesap ancak adres kanıtından sonra eşleştirilir; yeni adres kanıtı bekleyen
profili günceller ve `/kayit/google` ekranına döner. Doğrulama yanıtında
`status:authenticated|profile_required` kullanılır. Süresi dolmuş/yabancı oturumdaki
kanıt reddedilir. Kullanıcı ilk Google akışından yeniden başlayabilir.

## GitHub giriş/kayıt ve hesap bağlama — 18 Eylül 2026

GitHub OAuth App yalnız `user:email` ister; repo izni istemez ve sağlayıcı token'ını
kalıcı saklamaz. HTTPS code exchange PKCE S256 kullanır. `/user` içindeki kalıcı
sayısal ID kimlik kaynağıdır; otomatik e-posta eşleştirme yalnız `/user/emails`
yanıtındaki birincil ve doğrulanmış adresten yapılır. Public profil e-postası yeterli
değildir. Eksik adres FIRST mailbox doğrulamasına yönlenir.

| Metot / yol | Girdi | Sonuç |
|---|---|---|
| POST github/start/ | remember_me?:boolean, purpose?:login veya link | CSRF; `{authorization_url}`. Link için oturum + yakın kanıt gerekir |
| GET github/callback/ | code,state veya error,state | Tek kullanımlı, tarayıcıya bağlı state; `{status:authenticated veya profile_required veya linked,user?}` |
| GET github/signup/ | — | `{profile:{email,full_name,username,birth_date,gender,phone},email_verified,email_editable}` |
| POST github/signup/ | full_name,username,birth_date,gender,phone?,email? | CSRF; şifresiz profil tamamlama, 201 `{user}` |
| POST github/email/request/ | email | Bekleyen kayıtta doğrulanmamış/eksik adres için FIRST bağlantısı |
| POST github/email/verify/ | key | Aynı bekleyen tarayıcıda açık onay; `{status:authenticated veya profile_required,user?}` |

Sabit frontend callback `/accounts/github/login/callback/`; mevcut giriş `/`, yeni
kayıt `/kayit/github`, hesap bağlama `/hesap` yönüne gider. Posta kanıt ekranı
`/github-eposta-dogrula?key=…`; GET tek başına onaylamaz. Profilde GitHub adı ve
kullanıcı adı önerilir (GitHub kullanıcı adındaki tire alt çizgiye çevrilir); doğum
tarihi/cinsiyet gibi alınamayan zorunlu bilgiler kullanıcı tarafından doldurulur.

Hesabım ekranından GitHub bağlanabilir. Başlatma ve callback aynı oturum/kullanıcı,
güvenlik sürümü ve yakın yeniden doğrulamaya bağlıdır. Başka kullanıcıya bağlı
GitHub kimliği taşınmaz; mevcut farklı GitHub bağlantısı değiştirilmez. E-posta
farklı olsa bile bilinçli link akışı mevcut FIRST hesabına bağlar ve FIRST e-postasını
değiştirmez. Bağlantı kaldırma endpoint'i yoktur.

GitHub OAuth yeni şifre/ikinci faktör doğrulaması zamanını kanıtlamaz. Bu nedenle
`purpose:reauth` isteği `github_reauth_unavailable` ile reddedilir; GitHub girişinin
kendisi hassas işlemler için yakın kanıt oluşturmaz. Kullanıcı mevcut yerel şifresi
veya bağlı Google kimliğiyle yeniden doğrular. İkisi de yoksa mevcut şifre sıfırlama
akışıyla yerel şifre oluşturabilir. Hesap bağlama çatışması `github_link_conflict`,
eski bekleyen kayıt `github_signup_expired` ile bildirilir.

Kaynaklar: [GitHub OAuth akışı](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps),
[e-posta API'si](https://docs.github.com/en/rest/users/emails).

## Bağlı hesap görünümü

`User.connected_accounts`, yalnız mevcut kullanıcının bağlı Google/GitHub
kimliklerini gösteren bir dizidir. Mevcut `providers` alanı korunur. Her öğe:
`{provider, display_name, username, email, avatar_url, profile_url}`; görüntüleme
alanları string olup sağlayıcı verisi yoksa boş olabilir. GitHub kullanıcı adı
sağlayıcıdaki özgün addır; FIRST kullanıcı adıyla karıştırılmaz. Google e-postası
sağlayıcıdan alınan adrestir; eski kayıtta eksikse FIRST e-postasından türetilmez.

Bu alanlar yalnız görüntüleme içindir; hesap sahipliği/eşleştirme ve doğrulama
kararlarında kullanılmaz. Ham sağlayıcı yanıtı, erişim token'ı veya başka kullanıcı
verisi döndürülmez. Hesap sayfası okunurken harici sağlayıcı isteği yapılmaz.

## Confirmed account reset controls

All routes below require authenticated session, CSRF and recent authentication (10 minutes). Existing `reauthentication_required` handling applies; no automatic mutation retry after proof.

| Method/path | Body | Effect |
| --- | --- | --- |
| POST `github/disconnect/` | `{"confirmation":"GITHUB"}` | Remove GitHub identity and repository grant; archive shares. Another login method required (`last_login_method`). |
| POST `projects/github/disconnect/` | `{"confirmation":"REPO"}` | Revoke GitHub App user grant, remove credential, archive shares; keep login identity. |
| DELETE `account/` | `{"confirmation":"HESABIMI SIL"}` | Revoke stored App grant, delete FIRST user and cascaded data, invalidate sessions and logout. |

Disconnect returns `{detail,user}`; account deletion returns `{detail}`. Repository status includes `credential_stored` independently from current provider connectivity so stale credentials can be cleared. Disconnect preserves the current session and invalidates other sessions and pending provider flows. GitHub App installations, GitHub repositories and the GitHub account are never deleted. Discarded login OAuth tokens cannot be revoked server-side; the UI links to GitHub consent settings for a full external authorization reset. Known provider revocation failure does not block local data removal: responses include `github_cleanup_required: true` and a warning to revoke remaining access in GitHub settings. `github_authorization_revoked` is true for confirmed revocation, false for failure, null when no stored credential existed. Confirmations explain this limitation, and the deletion redirect retains the cleanup warning.

## GitHub repository onboarding during authentication

Successful GitHub login/link/signup and email-verification authentication enter
`/github-kurulum`. Existing GitHub OAuth identity and App permission boundaries
remain separate internally; no broad OAuth `repo` scope is requested.

`POST projects/github/start/` accepts optional `return_to` from `/`, `/hesap`,
`/projelerim/yeni` (default). It is state-bound and returned by the callback,
not taken from callback query parameters. Frontend validates destinations again.
App start/callback and own-repository inventory require authenticated linked
GitHub identity. Preview/create retain verified-email guards. Existing status
and repository APIs determine readiness; installation callback query values are
never trusted as ownership proof. Cancellation, empty installation return and
provider errors stop automatic redirects and offer explicit recovery.

19 Eylül doğrudan IP revizyonunda yalnız kaynak/diff incelemesi yapıldı. Önceki test kanıtları yeni transport için çalışma zamanı doğrulaması sayılmaz.
