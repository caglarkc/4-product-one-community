# FIRST — Kayıt, giriş ve hesap bağlantısı kararları

Kayıt tarihi: 17 Eylül 2026. Kaynak: kullanıcının auth görüşmesindeki açık kararları. Kabul edilmiş ürün ve auth tasarım kararlarıdır. Normal auth, hesap yönetimi ve Google entegrasyonu uygulandı; GitHub entegrasyonu 18 Eylül 2026 görevinde eklenmektedir. Güncel uygulama sözleşmesi: `contracts/auth-api.md`.

## 1. Giriş ve kayıt yöntemleri

- E-posta + şifre, Google ve GitHub ile kayıt/giriş olacak.
- Tüm yöntemler normal kullanıcı hesabı oluşturur. Öğrenci olmak temel katılım şartı değildir.
- Google eşleştirmesi yalnız Google ile giriş/kayıt sırasında yapılır; uygulama içinde Google bağlama seçeneği yoktur (18 Eylül 2026 güncellemesi). GitHub bağlama kararı korunur.
- Dört ürün ayrı siteler olacak; hesaplar ileride ortak kullanılacak.

## 2. Normal kayıt alanları

| Alan | Koşul |
|---|---|
| Ad soyad | Zorunlu |
| Kullanıcı adı | Zorunlu |
| E-posta | Zorunlu |
| Şifre | E-posta kaydında zorunlu |
| Telefon | Kayıtta isteğe bağlı |
| Doğum tarihi | Zorunlu; 13 yaşından küçükler kayıt olamaz |
| Cinsiyet | Zorunlu seçim; “Belirtmek istemiyorum” bulunacak |

Google/GitHub kaydında sağlayıcıdan gelmeyen zorunlu profil bilgileri ilk girişte profil tamamlama ekranında alınır. Sosyal giriş kullananlardan ayrıca yerel şifre isteme kararı alınmadı.

## 3. E-posta doğrulama akışı

- Normal kayıt sonrası e-postaya doğrulama bağlantısı gönderilir.
- Kullanıcı hemen doğrulamak zorunda değildir; giriş yapabilir ve üstte doğrulama hatırlatması görür.
- Repo başvurusu yapmak ve repo ilanı oluşturmak için e-posta doğrulanmış olmalıdır.
- Kullanıcı Google/GitHub girişinde tekrar doğrulama e-postası istemiyor.
- Teknik koşul olarak görüşmede şu ayrım belirtildi: sağlayıcıdan güvenilir biçimde doğrulanmış e-posta alınmışsa tekrar doğrulama yapılmaz. Adres gelmezse veya doğrulanmış olduğu teyit edilemezse bu istisna uygulanamaz; kullanıcıdan e-posta alınır ve FIRST doğrulama bağlantısı gönderilir. Kullanıcı bu sırada normal kayıttaki gibi doğrulama gerektirmeyen alanlara erişebilir; mevcut hesapla eşleşen adres doğrulanmadan o hesaba erişim verilmez. Yalnızca sosyal giriş yapılmış olması her adresi otomatik doğrulanmış saydırmaz.

## 4. İşlem koşulları

| İşlem | Kararlaştırılan koşullar |
|---|---|
| Herkese açık projeleri gezmek | Hesap gerekmiyor |
| Public repo ilanına başvurmak | Hesap, doğrulanmış e-posta ve bağlı GitHub hesabı |
| GitHub üzerinde katkı/PR işlemleri | Bağlı GitHub hesabı ve işlemin gerektirdiği GitHub izinleri; öğrenci doğrulaması şart değil |
| Repo ilanı eklemek | Doğrulanmış e-posta, bağlı GitHub ve repo sahibi/yetkili yönetici olma; test aşamasında telefon şartı yok |

Telefon doğrulaması normal kullanıcının başvuru yapması için şart değildir. 19 Eylül 2026 test aşaması kararıyla repo ilanı ekleme sırasında telefon numarası veya telefon doğrulaması aranmaz. Telefon alanı isteğe bağlı kalır; numaranın dolu veya boş olması işlem yetkisini etkilemez. Buradaki “repo oluşturma”, mevcut GitHub reposunu FIRST'e bağlayıp ilan oluşturma anlamındadır; GitHub'da yeni repo oluşturan API kararlaştırılmadı. Private repolarda katılımın yalnız davetle olması kuralı korunur.

## 5. Telefon

- Aynı telefon numarası iki hesapta doğrulanmış olarak kullanılamaz; tek hesaba bağlanabilir. Doğrulanmadan girilen numara, gerçek sahibinin ileride doğrulayarak kullanmasını engellemez.
- Doğrulama SMS veya WhatsApp olabilir. Kanal ve sağlayıcı seçilmedi; uygunluk ve maliyet değerlendirilecek.
- Telefon değişince doğrulama durumu sıfırlanır. Numara devri ve kurtarma ayrıntıları sağlayıcı entegrasyonunda netleştirilecektir.

## 6. Hesap bağlama

- E-postayla veya Google ile kayıt olan kullanıcı, repo başvurusu/ilan oluşturma öncesinde GitHub'ı bağlamalıdır.
- GitHub hesabını mevcut oturumdan aynı kullanıcı hesabına bağlama kabul edildi. Google için bu karar 18 Eylül 2026 tarihinde kaldırıldı; Google yalnız giriş/kayıt sağlayıcısıdır.
- Google/GitHub tarafından güvenilir biçimde doğrulanmış e-posta mevcut FIRST hesabıyla eşleşirse otomatik giriş ve sağlayıcı bağlama yapılır. Önce mevcut hesaba ayrıca giriş istenmez. Önceki otomatik eşleştirmeme önerisi geçersizdir.
- Sağlayıcı e-postası eksik veya doğrulanmamışsa FIRST e-posta doğrulaması tamamlanmadan mevcut hesaba erişim verilmez.
- Sonraki sosyal girişlerde sağlayıcının değişmeyen kullanıcı ID'si esas alınır.
- Bir Google/GitHub hesabı yalnızca bir FIRST hesabına bağlı olabilir; başka hesaba bağlı kimlik sessizce taşınmaz.
- Önceden doğrulanmamış FIRST hesabına otomatik eşleştirme yapılınca eski oturumlar kapatılır; önceki yerel şifre yenilenmeden kullanılamaz.
- 19 Eylül 2026 test süreci kararı: Hesabım ekranından GitHub hesap bağlantısı ve GitHub repo erişimi ayrı işlemlerle kaldırılabilir. Bu karar önceki GitHub bağlantısını kaldıramama kararını geçersiz kılar. Google bağlantısını ayrı kaldırma bu kapsamda değildir.
- GitHub ile giriş ve repo üzerinde işlem yapma izinlerinin kapsamı ayrı tasarlanacak; girişin tek başına tüm repolarda yetki verdiği varsayılmaz.

## 7. GitHub'dan alınabilecek bilgiler — araştırma notu

Görüşmede resmî dokümanlarla kontrol edildi:

- `GET /user`: kullanıcı ID'si, kullanıcı adı, avatar ve doldurulmuşsa isim/biyografi/konum gibi profil alanları. İsim doğrulanmış yasal kimlik değildir.
- `GET /user/emails`: uygun izinle gizli adresler dahil hesaba bağlı e-postalar; `primary`, `verified`, `visibility` alanları.
- OAuth App için `user:email`; GitHub App kullanıcı erişimi için “Email addresses: read” izni gerekir. 18 Eylül 2026: kullanıcı OAuth App oluşturdu; giriş için OAuth App seçildi. Repo işlemlerinin izin tasarımı ayrı kalır.
- Ayrı bir “güvenlik/kurtarma e-postası” alanı varsayılmaz. Birincil doğrulanmış e-postayı seçmek mümkündür.
- GitHub ID ile hesap eşleştirmek, ad/avatar ile profili doldurmak ve gizli e-postayı public profilde yayımlamamak önerildi. Kesin veri saklama şeması henüz oluşturulmadı.

Kaynaklar: [GitHub kullanıcı API'si](https://docs.github.com/en/rest/users/users#get-the-authenticated-user), [e-posta API'si](https://docs.github.com/en/rest/users/emails), [OAuth izinleri](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps).

## 8. Ayrı kalan konu: öğrenci doğrulaması

Hesap e-postası doğrulaması, telefon doğrulaması ve aktif öğrenci doğrulaması ayrı şeylerdir. Öğrencilik temel kayıt veya repo katılımı şartı yapılmadı. Sağlayıcı araştırması [ayrı nottadır](ogrenci-dogrulama-arastirmasi.md); SheerID satın alma/entegrasyon kararı yoktur.

## 9. Şifre ve kurtarma

- Şifre en az 8, en fazla 20 karakterdir. Boşluk kabul edilmez; büyük harf, küçük harf, sayı ve özel karakter zorunludur.
- Türkçe karakterler kabul edilir. Yaygın ve ele geçirilmiş şifreler reddedilir; periyodik zorunlu şifre değişimi yoktur.
- Şifre sıfırlama bağlantısı 30 dakika geçerli ve tek kullanımlıktır. Başarılı sıfırlama bütün oturumları kapatır; yeniden giriş gerekir.
- Sıfırlama isteği hesap varlığını açıklamayan genel cevap döndürür.
- Sosyal kayıtla başlayan kullanıcı doğrulanmış e-postası üzerinden yerel şifre oluşturabilir.

## 10. E-posta gönderimi ve değişikliği

- Doğrulama bağlantısı 24 saat geçerlidir. Yeniden gönderimler arasında 60 saniye beklenir; adres başına saatte en fazla 5 gönderim yapılır.
- Süresi dolan bağlantı ekranında yenisini isteme seçeneği bulunur.
- E-posta SMTP üzerinden gönderilir. SMTP hizmeti, gönderen domain, kota ve maliyet koşulları henüz doğrulanmadı; ücretli hizmet satın alma kararı yoktur.
- E-posta değişikliğinde yeni adres doğrulanana kadar eski adres geçerlidir; eski adrese değişiklik bildirimi gönderilir.
- Yeni adres başka hesaptaysa e-posta değiştirme işlemi hesapları birleştirmez. Bu işlem sosyal girişte otomatik eşleştirmeden ayrıdır.

## 11. Oturum ve deneme sınırları

- Normal oturum 24 saat; “Beni hatırla” ile 30 gündür.
- Kullanıcı açık oturumlarını görebilir, tek tek veya topluca kapatabilir.
- E-posta ve şifre değişikliği gibi hassas işlemler için son 10 dakika içinde şifre veya sosyal sağlayıcıyla yeniden doğrulama gerekir. GitHub bağlantısı/repo erişimi kaldırma ve FIRST hesabını silme de bu koşula tabidir.
- Hesap başına 15 dakikada 5 başarısız şifre denemesinden sonra geçici bekleme uygulanır; ayrıca IP bazlı hız sınırı bulunur. Kalıcı hesap kilidi yoktur; eşikler ayarlanabilir olacaktır.
- IP eşiği ve geçici beklemenin süresi teknik uygulamada netleştirilecektir.

## 12. Profil tamamlama

- Kullanıcı adı 3–30 karakterdir; harf, rakam ve alt çizgi içerir. Büyük/küçük harften bağımsız benzersizdir.
- Sosyal sağlayıcıdaki isim öneri olarak doldurulur; zorunlu alanlar tamamlanmadan başvuru ve ilan işlemleri açılamaz.
- En az 13 yaş koşulu hem normal hem sosyal kayıtta uygulanır.

## 13. Onaylanan mimari ve kalan ayrıntılar

- `contracts/auth-api.md` onaylanmış başlangıç sözleşmesidir; bu belgedeki sonraki kararlarla birlikte uygulanır. Önceki uzun API öneri listesinin tamamı onaylanmış kapsam değildir.
- Django/DRF kimlik ve yetki kaynağıdır; django-allauth sosyal girişleri yönetir. HttpOnly session cookie + CSRF ve Next.js üzerinden aynı origin proxy yaklaşımı kabul edildi.
- Kalıcı veriler PostgreSQL'de tutulacaktır. Auth işlemlerinde Redis kullanılacaktır; oturum, sayaç ve geçici veri sorumlulukları ile kalıcılık/arıza davranışı teknik uygulamada netleştirilecektir.
- Backend uzak sunucuda Docker içinde çalıştırılır. İlk aşama FIRST oturumudur; dört ürünün ortak oturum/SSO tasarımı ayrıdır.
- Telefon doğrulama kanalı/sağlayıcısı daha sonraya ertelendi. Test aşamasında ilan akışı telefon doğrulamasına bağlı değildir; telefon isteğe bağlıdır ve girilmesi doğrulanmış sayılmaz.
- Yeni kabul edilen oturum listeleme/sonlandırma, yeniden doğrulama, e-posta değiştirme ve sosyal kullanıcıya şifre oluşturma akışlarının endpoint/veri sözleşmeleri uygulama öncesinde tamamlanacaktır.

## 14. Google akışı — 18 Eylül 2026 kullanıcı güncellemesi

- Google ile giriş/kayıt aynı akıştır. Güvenilir biçimde doğrulanmış Google e-postası mevcut hesabın e-postasıyla eşleşirse, hesabın normal veya GitHub kaydıyla açılmış olmasına bakılmadan Google kimliği eşleştirilir ve giriş yapılır. Bölüm 6 güvenlik kuralları korunur.
- Eşleşen hesap yoksa henüz tamamlanmış hesap oluşturulmaz: kayıt tamamlama ekranı açılır. Sağlayıcıdan alınabilen bilgiler önceden doldurulur; eksik zorunlu alanlar kullanıcıdan alınır ve “Kaydı tamamla” ile kayıt tamamlanır.
- Google kaydında yerel şifre istenmez. Ad soyad, kullanıcı adı, doğum tarihi ve cinsiyet zorunlu; telefon isteğe bağlıdır. Sağlayıcıdan doğum tarihi/cinsiyet geldiği varsayılmaz veya sırf bunlar için ek Google API izni istenmez.
- Uygulama içinden Google bağlama/kaldırma ekranı veya endpoint'i yoktur. Başka Google hizmetlerine erişim kapsam dışıdır. Mevcut bağlı Google kimliğiyle hassas işlemler için yeniden doğrulama, hesap bağlama işlemi sayılmaz.
- Canlı callback: `https://first.alicaglarkocer.com/accounts/google/login/callback/`.

Teknik güvenlik koşulu: Google adres sahipliği kanıtı sağlamıyorsa bekleyen Google kaydı FIRST e-posta doğrulaması tamamlanana kadar nihai kullanıcı/sağlayıcı bağlantısı oluşturmaz. Bu, henüz doğrulanmamış adresle başka bir kişinin hesabına kalıcı sosyal erişim bırakılmasını önler; güvenilir Google e-postasında ek doğrulama yoktur.

## 18 Eylül 2026 — GitHub uygulama ayrıntısı

GitHub giriş/kayıt için OAuth App ve yalnız `user:email` izni kullanılır. Repo erişimi
ayrı App izniyle yürütülür; aşağıdaki güncel kararla giriş/bağlama akışına dahil edilir. GitHub kimliğiyle giriş, doğrulanmış birincil e-posta
ile eşleştirme, şifresiz profil tamamlama ve Hesabım ekranından GitHub bağlama uygulanır.
GitHub OAuth yeni kimlik doğrulama zamanını garanti etmediğinden hassas işlemler için
şifre veya bağlı Google hesabıyla yakın yeniden doğrulama gerekir; yalnız GitHub
kullanan kişi mevcut e-posta kurtarma akışıyla yerel şifre oluşturabilir.

## 19 Eylül 2026 — Repo erişimi ve test aşaması

- Telefon numarası ve telefon doğrulaması repo ilanı oluşturma koşulu değildir; test aşamasında tek iletişim doğrulama şartı e-postadır. GitHub bağlantısı ve seçilen reponun sahibi/yetkili yöneticisi olma şartları korunur.
- Kullanıcının son kararı önceki geniş OAuth `repo` izni tercihini geçersiz kılar. Mevcut GitHub OAuth giriş/bağlama akışı `user:email` ile kalır.
- Repo işlemleri ayrı bir GitHub App kurulumu üzerinden, kullanıcının seçtiği repolarda yürütülür. Kullanıcının tek repo seçebilmesi gerekir; bütün hesabın private repolarına erişim zorunlu tutulmaz.
- GitHub giriş/bağlama akışı GitHub App kurulumunu ve repo izin seçimini tamamlar; repo ekleme ekranı yalnız kurulumda erişim verilmiş repoları işlem için sunar. Kurulum callback parametreleri tek başına yetki kanıtı sayılmaz; kullanıcı/kurulum ilişkisi ve repo yönetim yetkisi GitHub API ile doğrulanır.
- Seçilen repolarda mevcut ürün akışlarının gerektirdiği okuma/yazma izinleri tanımlanır. Repo erişimi seçimi ile Contents, Pull requests, Issues ve Administration gibi işlem izinleri ayrı kontrol edilir. Hesap/organizasyon geneli yönetim izinleri bu kararın parçası değildir.
- GitHub App kaydı, seçilen repo doğrulaması ve şifreli dönen kullanıcı tokenları uygulanmıştır. Mevcut OAuth kimlikleri ve girişleri korunur.

## 16. Test sürecinde bağlantı ve hesap sıfırlama — 19 Eylül 2026

- Hesabım ekranında GitHub hesap bağlantısını kaldırma, repo erişimini kaldırma ve FIRST hesabını kalıcı silme ayrı onaylı işlemlerdir. Hesap silme için `HESABIMI SIL` yazılır.
- Repo erişimi kaldırıldığında GitHub App kullanıcı yetkilendirmesi iptal edilir, FIRST'teki şifreli erişim/yenileme bilgileri silinir ve paylaşımlar arşivlenir; GitHub ile giriş korunur. GitHub App kurulumu ayrı kalır; GitHub'daki kurulum ayarlarından yönetilir.
- GitHub hesap bağlantısı kaldırıldığında repo erişimi de temizlenir ve paylaşımlar arşivlenir. Kullanıcının başka giriş yöntemi (yerel şifre veya başka bağlı sağlayıcı) olmalıdır.
- Giriş OAuth uygulamasının anahtarı kalıcı tutulmadığından FIRST bağlantısını kaldırmak GitHub tarafındaki bu ayrı OAuth onayını iptal etmez. Baştan onay testi için GitHub Authorized OAuth Apps ayarından kaldırılır; arayüz bu ayrımı belirtir.
- FIRST hesabını silmek profil, bağlı sağlayıcı kayıtları, repo erişim bilgileri, paylaşımlar ve oturum kayıtlarını siler. GitHub hesabı veya repoları silinmez. Aynı e-postayla yeni kayıt tekrar denenebilir.
- Üç işlem de CSRF ve son 10 dakikada yeniden kimlik doğrulaması ister. Yalnız GitHub girişi olan kullanıcı mevcut e-posta kurtarma akışıyla şifre oluşturabilir; test için kimlik doğrulaması atlanmaz.
- GitHub yetki iptali denenir. Süresi dolmuş/geçersiz anahtar veya sağlayıcı arızası yerel temizliği engellemez; böyle bir durumda arayüz kalan iznin GitHub ayarlarından kaldırılması gerektiğini açıkça belirtir. Bağlantı kaldırma diğer oturumları ve bekleyen bağlantı akışlarını geçersiz kılar, mevcut oturumu korur.

## 17. GitHub girişinde repo izinlerini tamamlama — 19 Eylül 2026

- GitHub ile giriş, yeni kayıt tamamlanması ve mevcut FIRST hesabına GitHub bağlanması aynı repo kurulum akışına devam eder. Kullanıcıya sonradan iki ayrı repo bağlantısı butonu sunulmaz.
- Teknik olarak giriş OAuth App ve repo GitHub App ayrı kalır. İlk kullanımda kullanıcı GitHub yetkilendirme ve seçili repo kurulum ekranlarına sırayla gider; mevcut geçerli yetkiler varsa adımlar atlanır. GitHub izinleri kullanıcı yerine sessizce onaylanmaz.
- Repo ekleme ekranında erişime açılmış ve kullanıcının yönetim yetkisi bulunan repolar listelenir. Yeni repo erişime açmak için tek “Repo izinlerini yönet” işlemi bulunur. Eski/eksik bağlantılar tek tamamlama akışına yönlendirilir.
- Kurulumdan dönüşte hâlâ seçilebilir repo yoksa veya kullanıcı reddederse yönlendirme döngüsü oluşturulmaz; açıklama ve tekrar deneme gösterilir. FIRST oturumu korunur.
- App yetkilendirmesi ve kendi repo envanterini listeleme için bağlı GitHub kimliği yeterlidir. README önizleme, paylaşım oluşturma ve yayımlama için doğrulanmış e-posta şartı korunur.
- Giriş/bağlama sonrası dönüş yolu yalnız `/`, `/hesap` veya `/projelerim/yeni` olabilir; dış adres veya GitHub callback query bilgileri yetki kanıtı değildir.
