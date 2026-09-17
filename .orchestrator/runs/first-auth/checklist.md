# FIRST normal auth checklist

Kaynak gerçek: `run.json`. Kanıtlar: `results/`, `evidence/`; eski başarısız denemeler korunur.

Geçmiş başarısız denemeler silinmez. Aşağıdaki `failed` satırları geçmiş kanıttır; düzeltme ve yeni bağımsız kapılar ayrı düğümlerdedir. CLI toplu durumunun blocked kalması bu geçmişten kaynaklanabilir; güncel kabul için revision/review-r2/verify-r2/integration ve H sonuçları okunmalıdır.

## Korunan başarısız denemeler

- `backend`: results/backend-resume-audit.json
- `frontend`: results/frontend-resume-audit.json
- `c-review`: results/c-review-2026-09-17T12-35-00-681Z.json
- `e-review`: results/e-review-2026-09-17T12-45-24-543Z.json
- `e-verify`: results/e-verify-2026-09-17T12-45-55-263Z.json
- `f-review`: results/f-review-2026-09-17T14-32-12-534Z.json

Kapanış eşlemeleri: eski backend/frontend → legacy review + B/D; c-review → c-revision/c-review-r2/c-verify-r2; e-review/e-verify → e-revision/e-review-r2/e-verify-r2; f-review → f-revision/f-review-r2/f-verify-r2.

## A — Hazırlık

Düğüm: `a-preparation` — **done**; bağımlılık: contract

 - [x] Kaynak belgeleri, gerçek dosyaları ve mevcut değişiklikleri incele.
 - [x] Run graph, dosya sahiplikleri ve checklist oluştur.
 - [x] Mevcut sözleşmeyle bu görevin kapsamını karşılaştır.
 - [x] Gerekli endpoint/veri ve test sözleşmelerini tamamla.
 - [x] Teknik tercihleri ve test sınırlarını kaydet.

Kanıt: results/a-preparation-2026-09-17T12-24-25-790Z.json

## B — Normal login/register backend

Düğüm: `b-backend` — **done**; bağımlılık: a-preparation, backend

 - [x] Kullanıcı modeli, migration’lar ve gerekli auth altyapısını kur.
 - [x] Kayıt API’sini alan doğrulaması, yaş, şifre ve benzersizlik kurallarıyla uygula.
 - [x] Giriş, beni hatırla, oturum sorgulama ve çıkış API’lerini uygula.
 - [x] Session, CSRF ve deneme sınırlarını uygula.
 - [x] Kayıtta doğrulama e-postası üretme/gönderim çağrısını SMTP uyumlu altyapıya bağla.
 - [x] E-posta doğrulama endpoint’i ve web ekranını sonraki aşamaya bırak; gönderim hatasını sahte başarıyla gizleme.

Kanıt: results/b-backend-2026-09-17T12-33-13-919Z.json

## C — Backend login/register kontrol kapısı

Düğüm: `c-test` — **done**; bağımlılık: b-backend

 - [x] Geçerli kayıt/giriş ve oturum sonlandırmayı test et.
 - [x] Eksik alan, tekrar eden e-posta/kullanıcı adı ve yaş sınırını test et.
 - [x] Şifre uzunluk sınırlarını ve her zorunlu karakter koşulunu test et.
 - [x] Yanlış giriş, genel hata yanıtları ve deneme sınırlarını test et.
 - [x] Anonim login/register dahil CSRF’nin gerçekten uygulandığını test et; test istemcisinde CSRF kontrolünü açık kullan.
 - [x] Doğrulanmamış e-postayla izin verilen giriş davranışını test et.
 - [x] API durum kodlarını, cevap şemalarını ve hassas veri sızıntısını kontrol et.

Kanıt: results/c-test-2026-09-17T12-33-14-473Z.json

## C bağımsız review — geçmiş başarısız deneme

Düğüm: `c-review` — **failed**; bağımlılık: c-test

 - [ ] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/c-review-2026-09-17T12-35-00-681Z.json

## C bağımsız verify

Düğüm: `c-verify` — **done**; bağımlılık: c-test

 - [x] İlgili aşamanın bağımsız verify kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/c-verify-2026-09-17T12-35-39-823Z.json

## C backend–web geçiş sözleşmesi

Düğüm: `c-integration` — **done**; bağımlılık: c-review-r2, c-verify-r2, c-verify

 - [x] Alanlar, rotalar, hata/CSRF/session sözleşmesi sonraki aşamaya uyumlu; önceki kapılar geçti.

Kanıt: results/c-integration-2026-09-17T12-37-18-205Z.json

## D — Login/register web

Düğüm: `d-web` — **done**; bağımlılık: c-integration, frontend

 - [x] Mevcut frontend yoksa FIRST altında Next.js/TypeScript temelini oluştur.
 - [x] Sade, responsive ve erişilebilir login/register sayfalarını oluştur.
 - [x] Gerçek API, proxy, CSRF ve cookie akışını bağla.
 - [x] Alan hataları, genel hata, yüklenme, çift gönderim engeli ve başarı yönlendirmesini uygula.
 - [x] Beni hatırla ve oturum durumunu bağla.
 - [x] Sonraki aşamada oluşturulacak ana sayfa/profil hedefleri için geçici ve dürüst geçiş davranışı kullan; sahte tamamlanmış sayfa sunma.

Kanıt: results/d-web-2026-09-17T12-43-48-068Z.json

## E — Login/register web kontrol kapısı

Düğüm: `e-test` — **done**; bağımlılık: d-web

 - [x] Form davranışlarını ve API sözleşmesini bileşen/kod testleriyle doğrula.
 - [x] Başarı, hata, yüklenme, oturum yokluğu ve CSRF senaryolarını kontrol et.
 - [x] Lint, typecheck ve build kontrollerini çalıştır.
 - [x] Backend–frontend alan, rota, durum kodu ve cookie/proxy uyumunu incele.

Kanıt: results/e-test-2026-09-17T12-43-48-523Z.json

## E bağımsız review — geçmiş başarısız deneme

Düğüm: `e-review` — **failed**; bağımlılık: e-test

 - [ ] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/e-review-2026-09-17T12-45-24-543Z.json

## E bağımsız verify — geçmiş başarısız deneme

Düğüm: `e-verify` — **failed**; bağımlılık: e-test

 - [ ] İlgili aşamanın bağımsız verify kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/e-verify-2026-09-17T12-45-55-263Z.json

## E backend–web geçiş sözleşmesi

Düğüm: `e-integration` — **done**; bağımlılık: e-review-r2, e-verify-r2

 - [x] Alanlar, rotalar, hata/CSRF/session sözleşmesi sonraki aşamaya uyumlu; önceki kapılar geçti.

Kanıt: results/e-integration-2026-09-17T12-50-44-593Z.json

## F — Hesap yönetimi backend

Düğüm: `f-backend` — **done**; bağımlılık: e-integration

 - [x] Şifremi unuttum ve şifre sıfırlama API’lerini uygula.
 - [x] Şifre değiştirme ve hassas işlemlerde yeniden doğrulamayı uygula.
 - [x] Profil bilgilerini güncelleme API’sini uygula.
 - [x] E-posta doğrulama ve tekrar gönderim API’lerini tamamla.
 - [x] E-posta değiştirmede eski/yeni adres ve doğrulama kurallarını uygula.
 - [x] Telefon ekleme/değiştirmeyi doğrulamasız uygula.
 - [x] Oturum listeleme ve tekil/toplu sonlandırmayı uygula.
 - [x] Süre aşımı, tekrar kullanılan token, başka kullanıcının verisine erişim, limitler ve oturum iptallerini test et.
 - [x] SMTP mesaj içeriğini ve bağlantıları bellek içi e-posta testleriyle kontrol et.

Kanıt: results/f-backend-2026-09-17T14-30-11-560Z.json

## F bağımsız review — geçmiş başarısız deneme

Düğüm: `f-review` — **failed**; bağımlılık: f-backend

 - [ ] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/f-review-2026-09-17T14-32-12-534Z.json

## F bağımsız verify

Düğüm: `f-verify` — **done**; bağımlılık: f-backend

 - [x] İlgili aşamanın bağımsız verify kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/f-verify-2026-09-17T14-32-12-819Z.json

## F backend–web geçiş sözleşmesi

Düğüm: `f-integration` — **done**; bağımlılık: f-review-r2, f-verify-r2, f-verify

 - [x] Alanlar, rotalar, hata/CSRF/session sözleşmesi sonraki aşamaya uyumlu; önceki kapılar geçti.

Kanıt: results/f-integration-2026-09-17T14-34-31-773Z.json

## G — Ana sayfa, profil ve ilgili web akışları

Düğüm: `g-web` — **done**; bağımlılık: f-integration

 - [x] Şimdilik boş ana sayfayı oluştur; yalnız gerekli temel gezinme ve oturum kontrollerini ekle.
 - [x] Profil sayfasını gerçek kullanıcı verileriyle oluştur.
 - [x] Bilgi güncelleme, e-posta değişikliği ve doğrulamasız telefon ekleme/değiştirmeyi bağla.
 - [x] Şifremi unuttum, sıfırlama ve değiştirme formlarını/ekranlarını bağla.
 - [x] E-posta doğrulama bağlantısı ekranını, hatırlatmayı ve tekrar gönderimi bağla.
 - [x] Yeniden doğrulama ve oturum yönetimi arayüzlerini bağla.
 - [x] Giriş, çıkış ve kayıt yönlendirmelerini tamamla.
 - [x] Doğrulama e-postası bağlantısını açmak tek başına veri değişikliği yapmasın; kullanıcı onay formu göndersin.
 - [x] Form, hata, yüklenme, yetkisiz erişim ve süre dolması senaryolarını kod testleriyle doğrula.
 - [x] Lint, typecheck ve build kontrollerini tamamla.

Kanıt: results/g-web-2026-09-17T14-43-44-625Z.json

## H — Toplu kontrol ve teslim

Düğüm: `h-regression` — **done**; bağımlılık: g-web

 - [x] Bütün auth kapsamı için son regresyon kontrollerini çalıştır.
 - [x] Backend–web sözleşmeleri, route’lar, CSRF, session, izinler ve hata biçimlerini birlikte incele.

Kanıt: results/h-regression-2026-09-17T14-44-35-081Z.json

## H bağımsız review

Düğüm: `h-review` — **done**; bağımlılık: h-regression

 - [x] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/h-review-2026-09-17T14-47-08-441Z.json

## H bağımsız verify

Düğüm: `h-verify` — **done**; bağımlılık: h-regression

 - [x] İlgili aşamanın bağımsız verify kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/h-verify-2026-09-17T14-47-08-644Z.json

## H backend–web geçiş sözleşmesi

Düğüm: `h-integration` — **done**; bağımlılık: h-review, h-verify

 - [x] Alanlar, rotalar, hata/CSRF/session sözleşmesi sonraki aşamaya uyumlu; önceki kapılar geçti.

Kanıt: results/h-integration-2026-09-17T14-47-37-273Z.json

## H — Belgeler ve Git teslimi

Düğüm: `h-delivery` — **done**; bağımlılık: h-integration

 - [x] Bağımsız son review, verification ve integration sonuçlarını kaydet.
 - [x] Başarısız kontrolleri düzelt; ilgili testleri yeniden çalıştır.
 - [x] README, örnek ortam değişkenleri ve auth sözleşmesini gerçek uygulamayla eşitle.
 - [x] Yerel .venv, secret, test verisi ve geçici çıktıları Git dışında tut.
 - [x] Yapılmayan gerçek PostgreSQL/Redis/SMTP, tarayıcı E2E ve uzak ortam kontrollerini açıkça listele.
 - [x] Checklist ile graph durumlarını eşitle.
 - [x] Kabul edilmiş göreve ait değişiklikleri anlamlı commit’lerle teslim et.

Kanıt: results/h-delivery-2026-09-17T14-49-51-658Z.json

## Eski başarısız denemenin arşiv kapısı

Düğüm: `legacy-backend-review` — **done**; bağımlılık: backend

 - [x] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/legacy-backend-review-2026-09-17T12-27-46-414Z.json

## Eski başarısız denemenin arşiv kapısı

Düğüm: `legacy-frontend-review` — **done**; bağımlılık: frontend

 - [x] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/legacy-frontend-review-2026-09-17T12-27-46-592Z.json

## C Unicode kullanıcı adı uzunluğu düzeltmesi

Düğüm: `c-revision` — **done**; bağımlılık: c-review, b-backend

 - [x] NFC normalizasyonu uzunluk kontrolünden önce; alt/üst sınır regresyon testleri geçer.

Kanıt: results/c-revision-2026-09-17T12-36-13-863Z.json

## C düzeltme sonrası bağımsız review

Düğüm: `c-review-r2` — **done**; bağımlılık: c-revision

 - [x] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/c-review-r2-2026-09-17T12-36-51-435Z.json

## C düzeltme sonrası bağımsız verify

Düğüm: `c-verify-r2` — **done**; bağımlılık: c-revision

 - [x] İlgili aşamanın bağımsız verify kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/c-verify-r2-2026-09-17T12-37-17-762Z.json

## E Unicode form ve güvenilir proxy IP düzeltmesi

Düğüm: `e-revision` — **done**; bağımlılık: e-review, d-web, e-verify

 - [x] NFC kullanıcı girişi backend ile uyumlu; logout UI durumları test edildi.
 - [x] Güvenilir ingress IP için imzalı server-to-server aktarım ve spoof/expiry/config tests; varsayılan kullanıcı başlığına güvenilmez.

Kanıt: results/e-revision-2026-09-17T12-48-47-111Z.json

## E düzeltme sonrası bağımsız review

Düğüm: `e-review-r2` — **done**; bağımlılık: e-revision

 - [x] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/e-review-r2-2026-09-17T12-50-08-087Z.json

## E düzeltme sonrası bağımsız verify

Düğüm: `e-verify-r2` — **done**; bağımlılık: e-revision

 - [x] İlgili aşamanın bağımsız verify kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/e-verify-r2-2026-09-17T12-50-44-148Z.json

## F stale partial-save güvenlik düzeltmesi

Düğüm: `f-revision` — **done**; bağımlılık: f-review, f-backend

 - [x] Partial saves eski email/username ile yeni doğrulanmış veriyi ezmez; actual login signal regression ve auth suite geçer.

Kanıt: results/f-revision-2026-09-17T14-33-17-608Z.json

## F düzeltme sonrası bağımsız review

Düğüm: `f-review-r2` — **done**; bağımlılık: f-revision

 - [x] İlgili aşamanın bağımsız review kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/f-review-r2-2026-09-17T14-33-56-072Z.json

## F düzeltme sonrası bağımsız verify

Düğüm: `f-verify-r2` — **done**; bağımlılık: f-revision

 - [x] İlgili aşamanın bağımsız verify kontrolü; bulgular giderilmiş, kanıt kaydedilmiş olmalı.

Kanıt: results/f-verify-r2-2026-09-17T14-34-31-208Z.json

## Ortam sınırları

Gerçek PostgreSQL, Redis atomiklik/TTL/arıza, SMTP teslimi, dinleyen uygulama, tarayıcı E2E ve deploy: **not_verified** — kullanıcı kapsamı dışında.
