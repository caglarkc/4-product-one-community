# FIRST ana sayfa — seçenek 2

## Kanıt ve kapsam

- Kaynak görsel: `/Users/caglarkc/.codex/generated_images/01a0d81d-f348-7930-a39b-0c6cbd7d5536/exec-86224382-8041-49ef-9e3b-e760d30925b4.png`
- Uygulama: `http://127.0.0.1:3101/`, ziyaretçi, ilk sayfa, filtresiz.
- Masaüstü: `/Users/caglarkc/.codex/visualizations/first-home-option-2/desktop.png`
- Mobil: `/Users/caglarkc/.codex/visualizations/first-home-option-2/mobile.png`
- Kaynak 1487×1058 px; uygulama 1488×1058 px, CSS viewport 1488×1058, yakalama 1:1. Bir piksel genişlik farkı tasarım bulgusu olarak değerlendirilmedi. Mobil viewport 390×844.
- Kaynak ve masaüstü ekran görüntüsü aynı karşılaştırma girdisinde açıldı. Tam görünümde başlıklar, kontroller, etiketler ve satırlar okunabildiği için ayrı kırpma gerekmedi.

## Görsel değerlendirme

- Tipografi: Türkçe destekli mevcut sistem fontu korundu. Büyük ve kalın başlık, mavi proje başlığı, ikincil açıklama hiyerarşisi referansla uyumlu. Görseldeki raster yazının fontu kesin bilinmediğinden birebir font eşleşmesi iddia edilmiyor.
- Yerleşim: lacivert yan menü, üst hesap bağlantıları, üç temel filtre, sonuç başlığı ve üç sütunlu proje satırları uygulandı. Gerçek API'nin 12 kayıtlık sayfalaması korunduğundan referanstaki beş örnek satıra göre alt bilgi daha aşağıdadır.
- Renkler: beyaz yüzey, lacivert gezinme ve mavi aksiyonlar merkezi token'larla uygulanır. Alan kenarlıkları erişilebilirlik incelemesi sonrası koyulaştırıldı.
- Varlıklar: mevcut FIRST marka işareti korundu; standart arayüz ikonları lisansıyla birlikte Heroicons kütüphanesinden alındı. Yeni fotoğraf/illüstrasyon yok.
- İçerik: ana başlık ve alt başlık referansla aynı. Proje açıklamaları, kategoriler, katkı türleri ve tarih gerçek API'den gelir; görseldeki kurgusal etiketler eklenmedi. Uzun açıklamalar iki satırda kısalır; detay bağlantısı tam içeriğe açılır.

## İnceleme ve düzeltmeler

1. Kaynak incelemesinde alan kenarlığı kontrastı ve yan menüyü atlamayan skip bağlantısı bulundu. Kontrol kenarlığı `#858fa3` yapıldı; ana sayfanın skip hedefi `#home-content` olarak ayrıldı.
2. Düzeltme sonrası masaüstü yakalaması kaynakla birlikte incelendi. Mobilde yatay taşma olmadığı (`scrollWidth = innerWidth = 390`) ve skip bağlantısının `home-content` öğesine odaklandığı doğrulandı.
3. Kategori filtresi 20 projeden 10 web projesine geçti. Ek filtrelerin açılması, filtre sıfırlama, ikinci sayfaya geçiş ve geri dönüş çalıştı. Ekipler sayfasına geçişte ana sayfa kabuğunun uygulanmadığı görüldü.
4. Tarayıcı hata/uyarı konsolunda kayıt yoktu. Test, lint, typecheck ve yerel üretim build'i çalıştırılmadı. Oturum açmış kullanıcı görünümü kaynak üzerinden incelendi; tarayıcıda doğrulanmadı.

## Kalan bulgu

- **P1 — Mevcut canlı metin arama API'si hata veriyor.** `GET /api/auth/projects/?page=1&q=pairproof` doğrudan HTTP 500 döndü; arayüz hata ve tekrar deneme durumunu gösteriyor. Bu frontend revizyonunda API istemcisi ve backend değiştirilmedi. Tasarımda açık P0/P1/P2 fark kalmadı, ancak uçtan uca arama doğrulaması bu backend sorunu nedeniyle tamamlanamadı.

## Uygulama kontrol listesi

- [x] Seçilen ana sayfa görünümü ve mobil uyarlama.
- [x] Kaynak incelemesi, görsel karşılaştırma, temel filtre/sayfalama kontrolleri.
- [ ] Canlı backend metin arama hatasının ayrı kapsamda giderilmesi.

final result: blocked
