# FIRST — Kayıt, giriş ve hesap bağlantısı kararları

Kayıt tarihi: 17 Eylül 2026. Kaynak: kullanıcının auth görüşmesindeki açık kararları. Kabul edilmiş ürün ve auth tasarım kararlarıdır. Normal auth ve hesap yönetimi uygulandı; Google/GitHub ve hesap eşleştirme gelecek kapsamdır. Güncel uygulama sözleşmesi: `contracts/auth-api.md`.

## 1. Giriş ve kayıt yöntemleri

- E-posta + şifre, Google ve GitHub ile kayıt/giriş olacak.
- Tüm yöntemler normal kullanıcı hesabı oluşturur. Öğrenci olmak temel katılım şartı değildir.
- Kullanıcı mevcut hesabına Google ve GitHub bağlayabilir.
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
| Repo ilanı eklemek | Doğrulanmış e-posta, bağlı GitHub, repo sahibi/yetkili yönetici olma ve doğrulanmış telefon |

Telefon doğrulaması normal kullanıcının başvuru yapması için şart değildir. Repo ilanı ekleme aşamasında telefonu olmayan kullanıcıdan numara ve doğrulama istenir. Buradaki “repo oluşturma”, mevcut GitHub reposunu FIRST'e bağlayıp ilan oluşturma anlamındadır; GitHub'da yeni repo oluşturan API kararlaştırılmadı. Private repolarda katılımın yalnız davetle olması kuralı korunur.

## 5. Telefon

- Aynı telefon numarası iki hesapta doğrulanmış olarak kullanılamaz; tek hesaba bağlanabilir. Doğrulanmadan girilen numara, gerçek sahibinin ileride doğrulayarak kullanmasını engellemez.
- Doğrulama SMS veya WhatsApp olabilir. Kanal ve sağlayıcı seçilmedi; uygunluk ve maliyet değerlendirilecek.
- Telefon değişince doğrulama durumu sıfırlanır. Numara devri ve kurtarma ayrıntıları sağlayıcı entegrasyonunda netleştirilecektir.

## 6. Hesap bağlama

- E-postayla veya Google ile kayıt olan kullanıcı, repo başvurusu/ilan oluşturma öncesinde GitHub'ı bağlamalıdır.
- Google/GitHub hesabını mevcut oturumdan aynı kullanıcı hesabına bağlama kabul edildi.
- Google/GitHub tarafından güvenilir biçimde doğrulanmış e-posta mevcut FIRST hesabıyla eşleşirse otomatik giriş ve sağlayıcı bağlama yapılır. Önce mevcut hesaba ayrıca giriş istenmez. Önceki otomatik eşleştirmeme önerisi geçersizdir.
- Sağlayıcı e-postası eksik veya doğrulanmamışsa FIRST e-posta doğrulaması tamamlanmadan mevcut hesaba erişim verilmez.
- Sonraki sosyal girişlerde sağlayıcının değişmeyen kullanıcı ID'si esas alınır.
- Bir Google/GitHub hesabı yalnızca bir FIRST hesabına bağlı olabilir; başka hesaba bağlı kimlik sessizce taşınmaz.
- Önceden doğrulanmamış FIRST hesabına otomatik eşleştirme yapılınca eski oturumlar kapatılır; önceki yerel şifre yenilenmeden kullanılamaz.
- Kullanıcı Google/GitHub bağlantısını kaldıramaz; bağlantı kaldırma ekranı ve endpoint'i olmayacaktır.
- GitHub ile giriş ve repo üzerinde işlem yapma izinlerinin kapsamı ayrı tasarlanacak; girişin tek başına tüm repolarda yetki verdiği varsayılmaz.

## 7. GitHub'dan alınabilecek bilgiler — araştırma notu

Görüşmede resmî dokümanlarla kontrol edildi:

- `GET /user`: kullanıcı ID'si, kullanıcı adı, avatar ve doldurulmuşsa isim/biyografi/konum gibi profil alanları. İsim doğrulanmış yasal kimlik değildir.
- `GET /user/emails`: uygun izinle gizli adresler dahil hesaba bağlı e-postalar; `primary`, `verified`, `visibility` alanları.
- OAuth App için `user:email`; GitHub App kullanıcı erişimi için “Email addresses: read” izni gerekir. Uygulama türü henüz seçilmedi.
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
- E-posta ve şifre değişikliği gibi hassas işlemler için son 10 dakika içinde şifre veya sosyal sağlayıcıyla yeniden doğrulama gerekir. Sağlayıcı bağlantısı kaldırma kapsamda değildir.
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
- Telefon doğrulama kanalı/sağlayıcısı ilan akışından önce seçilecektir. İlk auth aşamasında telefon isteğe bağlıdır ve doğrulanmış sayılmaz.
- Yeni kabul edilen oturum listeleme/sonlandırma, yeniden doğrulama, e-posta değiştirme ve sosyal kullanıcıya şifre oluşturma akışlarının endpoint/veri sözleşmeleri uygulama öncesinde tamamlanacaktır.
