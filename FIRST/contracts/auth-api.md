# FIRST normal auth API sözleşmesi

17 Eylül 2026. Ürün kararları: [auth-kararlari.md](../auth-kararlari.md). Bu belge uygulanmış normal auth davranışını tanımlar. Google/GitHub OAuth, bağlantı/eşleştirme, ortak ürün SSO'su, ilan/repo ve öğrenci doğrulama kapsam dışıdır. Sosyal giriş kararları gelecekte uygulanacaktır; aktif sosyal endpoint veya bağlantı kaldırma ekranı yoktur.

## Taşıma ve kimlik

Django + DRF yetki kaynağıdır. Next.js yalnız `/api/auth/*/` yollarını server-only sabit `BACKEND_URL` origin'ine proxy eder. Tarayıcı aynı origin üzerinden HttpOnly session cookie ve CSRF kullanır; bearer token veya localStorage kimliği yoktur. Son slash zorunludur. Bütün mutation'lar anonim kayıt/giriş/reset/doğrulama dahil CSRF cookie ve `X-CSRFToken` gerektirir. Web her mutation öncesi `csrf/` alır. Yanıtlar `Cache-Control: no-store` taşır.

Production kalıcı veri PostgreSQL'de kullanıcı ve oturum iptal kayıtlarıdır. Redis oturum içeriğini, deneme sayaçlarını ve anahtarı hash'lenmiş süreli token'ları tutar; process-local production fallback yoktur. Normal oturum 24 saat, `remember_me=true` 30 gün; süre mutlak, etkinlikle uzamaz. Her istek kalıcı oturum kaydı, süre ve kullanıcı güvenlik sürümünü kontrol eder. Doğrulanmamış e-postayla giriş serbesttir; web hatırlatma gösterir.

## Yanıt ve alanlar

Kullanıcı yanıtı `{user: User}`; `me/` anonim durumda `{user:null}` döner. `User`:

```text
id: number; email, username, full_name, phone: string
birth_date: ISO date | null
gender: female | male | other | unspecified | ''
email_verified, phone_verified, profile_complete: boolean
providers: []
capabilities: {can_apply:false, can_create_listing:false}
```

İlan/başvuru henüz uygulanmadığından capabilities false'dur; gelecekteki yetki garantisi değildir. Şifre hash'i, session key, token, security_version ve iç servis bilgileri kullanıcı yanıtına girmez.

Hata biçimi `{detail:string, errors?:Record<string,string[]>, code?:string}`. Alan doğrulaması ve yanlış şifre 400; korumalı oturumsuz istek 401; CSRF 403 `csrf_failed`; son 10 dakikada şifre kanıtı eksikse 403 `reauthentication_required`; geçersiz/eski/kullanılmış token 400 `invalid_token`; yabancı/yok oturum 404; limit 429; Redis/SMTP servis sorunu 503. Reset isteği SMTP istisnası aşağıdadır. Bilinmeyen mutation alanları reddedilir. İç hata ayrıntıları ve secret gönderilmez.

## Endpoint'ler

Tüm yollar `/api/auth/` altındadır. JSON nesnesi gönderilir; boş mutation `{}`. “Yakın kanıt”, mevcut oturumda son 10 dakika içinde şifreyle yeniden doğrulamadır.

| Metot / yol | Girdi | Başarı ve yetki |
|---|---|---|
| GET csrf/ | — | 200 `{csrfToken}` + CSRF cookie; anonim |
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

Next proxy Cookie/Origin/Referer/X-CSRFToken ve ayrı Set-Cookie başlıklarını korur; backend yönlendirmelerini takip etmez. Upstream timeout30s, SMTP timeout işlem başına10s. HTTPS, Secure cookie ve frontend origin için backend `CSRF_TRUSTED_ORIGINS` gerekir. Secret'lar yalnız ortam değişkenlerindedir; `.env.example` gerçek değer içermez.

Varsayılan IP kaynağı backend REMOTE_ADDR'dır; proxy arkasında ortak IP bütçesi oluşur. İsteğe bağlı per-client modda iki tarafta aynı server-only `AUTH_PROXY_SECRET` (en az32 karakter), frontend'de trusted ingress'in overwrite ettiği `AUTH_CLIENT_IP_HEADER` gerekir. Next tek IP için `ip\nseconds\nMETHOD\n/api/auth/path/` üzerinde HMAC-SHA256 üretir; X-First-Client-IP/Time/Signature gönderir. Backend ±60s ve imzayı denetler; uygunsuz istek403 `invalid_proxy_assertion`. Secret yoksa gelen assertion başlıkları yok sayılır. Gerçek ingress güveni ve saat uyumu ayrıca doğrulanmalıdır.

## Test sınırı

Django süreç içi client, `enforce_csrf_checks=True`, izole SQLite, FakeRedis ve locmem mail; frontend bileşen/sözleşme/lint/typecheck/build kullanılır. Mock'lar yalnız testtedir. Gerçek PostgreSQL kilit/eşzamanlılık, Redis Lua/TTL/arıza, SMTP teslim/zamanlama, proxy-ingress/HTTPS-cookie, tarayıcı E2E/görsel kullanım, Docker/uzak servis/deploy **not_verified**. Kod testlerinin geçmesi canlı ortamın çalıştığı anlamına gelmez. Kanıt ve korunmuş başarısız denemeler: [run checklist](../../.orchestrator/runs/first-auth/checklist.md).

- E-posta değiştirme: hedef adresten bağımsız kullanıcı başına 60 saniye aralık ve 5/saat, istemci IP başına 30/15 dakika. Redis bu üç bütçeyi atomik ayırır; hedef adres bütçesi ayrıca uygulanır. Hedef/SMTP başarısızlığı rezervasyonu geri almaz.
