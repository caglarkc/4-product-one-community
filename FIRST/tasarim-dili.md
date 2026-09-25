# FIRST — ortak tasarım dili

20 Eylül 2026: Kullanıcı bütün FIRST arayüzünü kodlama ve GitHub ekosistemini yansıtan modern bir tasarımla yenilemeyi istedi. Bu karar 18 Eylül tarihli sıcak “Ortak Atölye” paletinin yerini alır. GitHub'dan esinlenen geliştirici arayüzü FIRST kimliğiyle uygulanır; GitHub logosu veya resmi ortaklık iddiası kullanılmaz.

25 Eylül 2026: Kullanıcının `stitch_first_topluluk_platformu_tasar_m` referansı, önceki koyu tema yönünün yerini alır. Proje keşfi, proje detayı ve kullanıcı profili ekranları temel alınır; ortak kontroller aynı açık temayı tüm FIRST ekranlarına taşır.

## Görsel yön

25 Eylül 2026 ana sayfa revizyonu: Kullanıcı sunulan tasarımlardan **2. seçeneği** seçti. İlk aşama yalnız `/` sayfasıdır; diğer ekranlar kullanıcı değerlendirmesinden sonra ele alınır. Ana sayfada lacivert sabit yan gezinme, beyaz içerik, büyük başlık, üç temel filtre ve yatay proje satırları kullanılır. Ek filtreler açılır; mobilde gezinme üstte dört sütuna, proje satırları tek sütuna geçer. Bu aşamanın token değerleri `body:has(.home-discovery)` altında, yerleşimi `home-discovery.css` içinde kapsamlandırılır. Ortak form bileşenleri, gerçek proje verisi ve sayfa başına 12 kayıt korunur. Aşağıdaki önceki yerleşim kararları diğer ekranlar için geçerlidir.

Açık lavanta çalışma alanı, beyaz paneller, koyu lacivert metin ve mavi birincil aksiyonlar. Yeşil yalnız olumlu durum ve davete açıklık gibi etiketlerde kullanılır. Referanstaki kompakt bilgi hiyerarşisi, ölçülü monospace etiketler ve hafif gölgeler korunur.

- Ana zemin `#faf8ff`, yüzey `#ffffff`, ikincil yüzey `#f2f3ff`, kenarlık `#e8e9f4`.
- Ana metin `#131b2e`, yardımcı metin `#596174`, bağlantı `#004ac6`, birincil aksiyon `#2563eb`.
- Başarı metni `#006c49`; hata ve disabled durumları açık temaya uygun ortak token kullanır.
- Panel köşeleri 12px, kontroller 8px; masaüstünde keşif üç sütun, tablette iki, mobilde tek sütun olur.
- Referanstaki örnek insanlar, avatar fotoğrafları, yıldız/katkı sayıları, API sağlık iddiası ve uygulanmamış navigasyon bağlantıları ürün verisi değildir; arayüze taşınmaz. Mevcut FIRST marka işareti ve sistem fontları korunur.

25 Eylül 2026 kompaktlık düzeltmesi: içerik kabuğu en fazla 1280px; gövde 14px, kart başlıkları 16px, sayfa başlıkları 22–28px. Panel iç boşlukları 16–20px, kart araları 16px. Profil avatarı 56px; geniş dekoratif üst alanlar yerine gerçek içerik öne çıkar. Masaüstü menü 1100px altında sarılır; proje keşfi 960px altında iki, 640px altında tek sütuna iner. Buton ve alanlar en az 44px kalır; mobil form alanları 16px yazıyla gösterilir. Alt bilgi tek ve kısa satır grubudur.

## Merkezi tanımlar

Değerlerin tek kaynağı `frontend/src/app/tokens.css`, tekrar kullanılan kontrollerin kaynağı `frontend/src/components/ui/` dizinidir. `globals.css` ortak kabuk ve düzen stillerini tanımlar. Yeni renkler semantik token olarak eklenir; sayfalarda kopya buton/form stilleri veya ayrı temalar oluşturulmaz.

Sistem fontları Türkçe karakterleri destekler, harici font indirmesi gerekmez. 4/8 tabanlı boşluk ölçeği, en az 44px hedefli kontroller, görünür klavye odağı, disabled/loading/error durumları ve `prefers-reduced-motion` desteği korunur. Yeni UI veya ikon bağımlılığı gerekmez; küçük dekoratif SVG'ler erişilebilirlik ağacından gizlenir.

## Ana sayfa ve proje kartları

Ana sayfa ziyaretçi ve üyeye tüm aktif topluluk paylaşımlarını sunar. En yeni paylaşımlar önce gelir; gerçek toplam ve sayfalama vardır. Proje sayısı az olduğunda sahte kartlarla doldurulmaz. Başlık, kısa açıklama, üst/alt kategori, proje aşaması ve güncelleme tarihi taranabilir kartlarda gösterilir. Kartın ana bağlantısı FIRST proje detayına gider. Yıldız/fork/dil/katkıcı metrikleri yalnız gerçek veri kaynağı ve ayrı kapsam olduğunda eklenebilir.

Public feed yalnız paylaşılmış proje metni ve sınıflandırmayı içerir. Repo URL/adı/gizliliği, README ve hesap verileri listede tahmin edilmez. Detay ekranındaki mevcut GitHub doğrulaması korunur. Liste boş, yükleniyor, hatalı veya sayfa değiştirme durumlarını açıkça gösterir.

## Referansa uyarlanan yerleşimler

- Keşif: kısa başlık, arama, açılır filtre alanı, kaldırılabilir aktif filtreler ve gerçek sonuç sayısı. Kartlarda kategori/aşama, başlık, açıklama, katılım etiketleri, sahip ve güncelleme tarihi.
- Proje detayı: üst başlık/aksiyon paneli; içerik ve katılım yan yana. Sahip yönetiminde geniş panel kullanılır; bütün API ve yetki kontrolleri korunur.
- Profil: kimlik ve davet alanı üstte; hakkında/beceri/ilgi alanları solda, gerçek paylaşımlar sağda. Dar ekranda tek sütuna iner.

## Bütün ekranlar

Gezinme, giriş/kayıt/kurtarma, hesap/güvenlik, GitHub kurulumu, projelerim, proje oluşturma/düzenleme ve detay aynı tasarım dilini kullanır. Giriş durumuna göre menü kuralları korunur. Her sayfanın mevcut işlevleri, native form prop'ları, hata mesajları, gizlilik onayı ve güvenlik kontrolleri korunur. Mobilde okuma sırası, sarılan menüler ve tek sütun düzenler kullanılır. Başlık, klavye ve gerçek bağlantı semantiği dekorasyona feda edilmez.

## Kontrol

Varsayılan kaynak/diff incelemesidir; kullanıcı istemedikçe test, lint/typecheck, yerel build veya tarayıcı çalıştırılmaz. Mevcut dağıtım kontrolleri teslimin parçasıdır. Görsel veya canlı kullanıcı akışı çalıştırılmadıysa doğrulanmış sayılmaz.
