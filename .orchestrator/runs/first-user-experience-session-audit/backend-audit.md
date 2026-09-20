# FIRST backend oturum denetimi

20 Eylül 2026. Salt okunur kaynak incelemesi; backend değiştirilmedi. Backend denetçisi ve bağımsız reviewer aşağıdaki iki bulguda mutabık. Çalışma zamanı doğrulaması yapılmadı.

## P1 — Google normal girişinde yakın kimlik kanıtı

`FIRST/backend/accounts/google_views.py:216` normal Google girişinde `start_session()` çağırır; `accounts/views.py:88` koşulsuz `reauthenticated_at` yazar. `google_views.py:93` auth_time kontrolünü yalnız `purpose=reauth` için yapar; satır 140'taki max_age de yalnız bu akıştadır. `account_views.py:37` son 600 saniyeyi yalnız bu yerel timestamp ile belirler.

Eski Google tarayıcı oturumuyla normal giriş tamamlandığında yeni kimlik kanıtı olmadan e-posta değişikliği, bağlantı kaldırma ve hesap silme için 10 dakikalık hassas işlem penceresi açılır. Şifre değiştirme ayrıca eski şifreyi kontrol eder; bu bulgu onu doğrudan atlatmaz. GitHub girişi `github_views.py:105` içinde aynı timestamp'i temizler.

Öneri: normal Google girişinde bu yakın kanıtı üretme; yalnız doğrulanmış taze sağlayıcı auth_time veya şifre kanıtı sonrası üret. Henüz uygulanmadı.

## P2 — Devam eden GitHub callback sırasında oturum iptali

`FIRST/backend/projects/views.py:161` içindeki son transaction, dış sağlayıcı çağrısından sonra kullanıcı güvenlik sürümünü ve bağlı GitHub hesabını kontrol eder, fakat session iptalini/süresini ve kullanıcı aktifliğini yeniden kontrol etmez. `accounts/account_views.py:282` tek oturum iptalinde yalnız revoked alanını günceller; security_version değişmez.

İptalden önce kabul edilmiş callback GitHub HTTP yanıtını beklerken kendi oturumu başka cihazdan iptal edilirse, callback kalıcı repo credential yazımını yine tamamlayabilir. Sonraki istekler reddedilir; bu bulgu oturumun yeniden canlanması veya iptalden sonra yeni callback kabulü değildir.

Öneri: credential yazımından önce locked_user kontrolü; iptal ve callback yazımlarında uyumlu kilitleme sırası. Henüz uygulanmadı.

## Kaynakta görülen korumalar

- FIRST JWT/access-refresh çifti yerine Redis opaque Bearer session kullanır. Girişte anahtar yenilenir; normal oturum 24 saat, hatırlanan oturum 30 gün mutlak süreye sahiptir (`accounts/views.py:80`).
- Redis TTL, SET XX ve SQL SessionRecord iptal/süre/security_version kontrolleri bulunur (`session_backend.py`, `middleware.py`). Redis arızasında yerel fallback yoktur.
- Şifre/e-posta değişimleri ve toplu iptal security_version üzerinden eski oturumları geçersiz kılar. Hassas yazımların çoğu locked_user ile tekrar kontrol edilir (`account_views.py`).
- Korumalı endpoint'lerde kimlik ve nesne sahipliği kontrolü vardır. CSRF anonim mutation'lar dahil session'a bağlıdır; CORS tam origin eşleştirmesi kullanır (`authentication.py`, `views.py`, `cors.py`, `projects/views.py`).
- OAuth state tek kullanımlı; binder ve PKCE bulunur. GitHub App sağlayıcı kimliği bağlı hesapla eşleştirilir.
- GitHub App repo erişimi ayrı access/refresh çifti kullanır. Şifreli depolama, access süresinden 60 saniye önce refresh, SQL satır kilidi ve dönen çiftin birlikte kaydı vardır (`projects/github.py:60`). Süresi dolan refresh veya sağlayıcı hatası erişimi reddeder.
- GitHub uzak yetki iptali denenir; arıza yerel temizliği engellemez, manuel kaldırma gereği döndürülür (`reset_views.py`).

## Sınırlar

Test, lint, typecheck, build, tarayıcı veya canlı istek çalıştırılmadı. Gerçek Redis TTL/arıza, PostgreSQL yarış/kilit, GitHub refresh/revocation ve tarayıcı geçişleri doğrulanmadı. LocalStorage Bearer saklama kabul edilmiş mimarinin XSS karşısındaki sınırlamasıdır; bu incelemede yeni bir XSS açığı saptanmadı. Bu rapor backend'in sorunsuz veya yayına hazır olduğu iddiası değildir.
