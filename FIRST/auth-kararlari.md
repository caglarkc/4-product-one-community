# FIRST — Kayıt, giriş ve hesap bağlantısı kararları

Kayıt tarihi: 17 Eylül 2026. Kaynak: kullanıcının auth görüşmesindeki açık kararları. Ürün kurallarıdır; henüz uygulanmış API veya güvenlik tasarımı değildir.

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
- Teknik koşul olarak görüşmede şu ayrım belirtildi: sağlayıcıdan güvenilir biçimde doğrulanmış e-posta alınmışsa tekrar doğrulama yapılmaz. Adres gelmezse veya doğrulanmış olduğu teyit edilemezse bu istisna uygulanamaz; eksik durumun ekran akışı uygulama öncesinde belirlenir. Yalnızca sosyal giriş yapılmış olması her adresi otomatik doğrulanmış saydırmaz.

## 4. İşlem koşulları

| İşlem | Kararlaştırılan koşullar |
|---|---|
| Herkese açık projeleri gezmek | Hesap gerekmiyor |
| Public repo ilanına başvurmak | Hesap, doğrulanmış e-posta ve bağlı GitHub hesabı |
| GitHub üzerinde katkı/PR işlemleri | Bağlı GitHub hesabı ve işlemin gerektirdiği GitHub izinleri; öğrenci doğrulaması şart değil |
| Repo ilanı eklemek | Doğrulanmış e-posta, bağlı GitHub, repo sahibi/yetkili yönetici olma ve doğrulanmış telefon |

Telefon doğrulaması normal kullanıcının başvuru yapması için şart değildir. Repo ilanı ekleme aşamasında telefonu olmayan kullanıcıdan numara ve doğrulama istenir. Buradaki “repo oluşturma”, mevcut GitHub reposunu FIRST'e bağlayıp ilan oluşturma anlamındadır; GitHub'da yeni repo oluşturan API kararlaştırılmadı. Private repolarda katılımın yalnız davetle olması kuralı korunur.

## 5. Telefon

- Aynı telefon numarası iki hesapta kullanılamaz; tek hesaba bağlanabilir.
- Doğrulama SMS veya WhatsApp olabilir. Kanal ve sağlayıcı seçilmedi; uygunluk ve maliyet değerlendirilecek.
- Telefon değiştirme, numara devri ve hesap kurtarma ayrıntıları henüz belirlenmedi.

## 6. Hesap bağlama

- E-postayla veya Google ile kayıt olan kullanıcı, repo başvurusu/ilan oluşturma öncesinde GitHub'ı bağlamalıdır.
- Google/GitHub hesabını mevcut oturumdan aynı kullanıcı hesabına bağlama kabul edildi.
- Aynı e-posta nedeniyle hesapları otomatik birleştirmeme, mevcut hesaba giriş yaparak bağlama yaklaşımı önerildi ve görüşme özetinde yer aldı. Hesap çakışması ve kurtarma prosedürü henüz ayrıntılandırılmadı.
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

## 9. Henüz seçilmeyen teknik ayrıntılar

Session/JWT ve ortak hesap mimarisi, auth kütüphanesi, şifre kuralları, bağlantı/kod süreleri, deneme limitleri, şifre sıfırlama ve oturum yönetimi ayrıntıları, e-posta/telefon değişiklikleri, sağlayıcı bağlantısını kaldırma ve endpoint/veri sözleşmeleri henüz kararlaştırılmadı. Önceki uzun API öneri listesinin tamamı kabul edilmiş kapsam olarak alınmaz.
