# Normal auth kontrol matrisi

Graph acceptance criterion'ları kaynak gerçektir. Bu matris reviewer ve verifier için test hedeflerini ayrıntılandırır; sonuç sütunu ilgili aşamanın evidence dosyasından okunur, plan kontrol geçti anlamına gelmez.

| Kapı | Dosyalar/görev | Gereken kanıt |
|---|---|---|
| C | backend model/migration/register | Zorunlu alanlar, doğum gününün tam 13 yaş sınırı, gelecek tarih, cinsiyet, opsiyonel telefon; email/username casefold tekrarları; migration drift |
| C | backend validators | 7/8/20/21 uzunluk; büyük/küçük/rakam/özel karakter ayrı ayrı eksik; Unicode Türkçe; whitespace; yaygın/breach corpus |
| C | backend API/session/security | Gerçek CSRF enforced client, anonim POST reddi, me anon/auth, login yanlış/bilinmeyen aynı yanıt, 5 hesap /30 IP sınırı; normal/remember expiry; logout; serialized user alanları |
| C | backend mail/settings | Locmem mesaj URL ve içerik, SMTP failure görünür; Redis failure fail-closed; no-store, Secure/HttpOnly/SameSite; PostgreSQL production SQLite test ayrımı |
| E | web formlar/API/proxy | Register alanları/remember, field errors/global error/503/429, pending ve çift submit, CSRF token/cookie transport, expired session, gerçek API yol eşlemesi; lint/typecheck/build |
| F | backend token/account API | Reset unknown/known aynı yanıt; 30dk/24saat sınır, tek kullanım, stale security version, tüm session iptali, reauth 10dk sınırı ve shared limit, cross-user revocation, profile whitelist |
| F | backend email/phone | Eski adres korunur, eskiye bildirim/yeniye verify, token supersede, unique recheck, email change logout, 60s/5saat limit, phone false, no token in JSON |
| G/H | web full account | Gerçek profil GET/PATCH, yeniden auth, phone false, tüm mail/reset/change/session controls; link GET mutation yok, kullanıcı POST onayı; loading/error/401/expiry/recovery; boş home |
| H | combined | Backend regression, migrations, web tests/lint/typecheck/build, source contract routes/types/proxy/cookie; bağımsız review+verify+integration |

Her evidence kaydı görev/dosyalar, çalıştırılan komut, sonuç/kanıt referansı, yapılmayan kontroller ve nedenini taşır. İlk hata çıktısı korunur; düzeltme/recheck ayrı kaydedilir. Başarısız kabul kapısı failed result + revision graph düğümüyle izlenir.

Not verified: PostgreSQL uniqueness/locking/transaction isolation; Redis gerçek Lua atomicity/TTL/eviction/outage; SMTP gerçek teslim/DNS; Next proxy + browser cookies/origin bütünleşmesi; tarayıcı keyboard/responsive/E2E; Docker/deploy/remote health. Kullanıcı bu çalışma zamanı kontrollerini kapsam dışında bıraktı.
