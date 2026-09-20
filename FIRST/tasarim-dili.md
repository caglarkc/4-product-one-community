# FIRST — ortak tasarım dili

20 Eylül 2026: Kullanıcı bütün FIRST arayüzünü kodlama ve GitHub ekosistemini yansıtan modern bir tasarımla yenilemeyi istedi. Bu karar 18 Eylül tarihli sıcak “Ortak Atölye” paletinin yerini alır. GitHub'dan esinlenen geliştirici arayüzü FIRST kimliğiyle uygulanır; GitHub logosu veya resmi ortaklık iddiası kullanılmaz.

## Görsel yön

Koyu grafit çalışma alanı; ince kenarlıklı repo panelleri, okunabilir açık metin, mavi bağlantılar, yeşil birincil aksiyonlar. Başlıklar ve içerik sade sistem sans; kategori, tarih, bölüm etiketi ve kod işaretlerinde ölçülü monospace. Geniş pazarlama panelleri yerine gerçek projeler, düzenli bilgi hiyerarşisi ve belirgin aksiyonlar öne çıkar.

- Ana zemin yaklaşık `#0d1117`, yüzeyler `#161b22` / `#1c2128`, kenarlık `#30363d`.
- Ana metin `#e6edf3`, yardımcı metin `#9da7b3`, bağlantı/odak `#79b8ff`.
- Yeşil birincil aksiyonlar okunaklı metinle kullanılır; normal metin 4.5:1, gerekli kontrol sınırı ve odak 3:1 kontrast hedefler. Dekoratif yüzey kenarlığı ile etkileşimli kontrol sınırı ayrı token'dır.
- Durum renkleri etiketlerle desteklenir. Aşama, repo gizliliği ve FIRST paylaşımının aktif/arşiv durumları birbirine karıştırılmaz.
- Köşeler kontrollü, gölgeler hafif; kalabalık gradient, dekoratif terminal çıktısı veya sahte aktivite kullanılmaz.

## Merkezi tanımlar

Değerlerin tek kaynağı `frontend/src/app/tokens.css`, tekrar kullanılan kontrollerin kaynağı `frontend/src/components/ui/` dizinidir. `globals.css` ortak kabuk ve düzen stillerini tanımlar. Yeni renkler semantik token olarak eklenir; sayfalarda kopya buton/form stilleri veya ayrı temalar oluşturulmaz.

Sistem fontları Türkçe karakterleri destekler, harici font indirmesi gerekmez. 4/8 tabanlı boşluk ölçeği, en az 44px hedefli kontroller, görünür klavye odağı, disabled/loading/error durumları ve `prefers-reduced-motion` desteği korunur. Yeni UI veya ikon bağımlılığı gerekmez; küçük dekoratif SVG'ler erişilebilirlik ağacından gizlenir.

## Ana sayfa ve proje kartları

Ana sayfa ziyaretçi ve üyeye tüm aktif topluluk paylaşımlarını sunar. En yeni paylaşımlar önce gelir; gerçek toplam ve sayfalama vardır. Proje sayısı az olduğunda sahte kartlarla doldurulmaz. Başlık, kısa açıklama, üst/alt kategori, proje aşaması ve güncelleme tarihi taranabilir kartlarda gösterilir. Kartın ana bağlantısı FIRST proje detayına gider. Yıldız/fork/dil/katkıcı metrikleri yalnız gerçek veri kaynağı ve ayrı kapsam olduğunda eklenebilir.

Public feed yalnız paylaşılmış proje metni ve sınıflandırmayı içerir. Repo URL/adı/gizliliği, README ve hesap verileri listede tahmin edilmez. Detay ekranındaki mevcut GitHub doğrulaması korunur. Liste boş, yükleniyor, hatalı veya sayfa değiştirme durumlarını açıkça gösterir.

## Bütün ekranlar

Gezinme, giriş/kayıt/kurtarma, hesap/güvenlik, GitHub kurulumu, projelerim, proje oluşturma/düzenleme ve detay aynı tasarım dilini kullanır. Giriş durumuna göre menü kuralları korunur. Her sayfanın mevcut işlevleri, native form prop'ları, hata mesajları, gizlilik onayı ve güvenlik kontrolleri korunur. Mobilde okuma sırası, sarılan menüler ve tek sütun düzenler kullanılır. Başlık, klavye ve gerçek bağlantı semantiği dekorasyona feda edilmez.

## Kontrol

Varsayılan kaynak/diff incelemesidir; kullanıcı istemedikçe test, lint/typecheck, yerel build veya tarayıcı çalıştırılmaz. Mevcut dağıtım kontrolleri teslimin parçasıdır. Görsel veya canlı kullanıcı akışı çalıştırılmadıysa doğrulanmış sayılmaz.
