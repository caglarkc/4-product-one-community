# STEP — Student Talent Entry Platform

Üniversite öğrencilerine özel, Upwork benzeri ücretli iş pazarı.

Durum: 30 Eylül 2026 görüşmesinde 52 ürün önerisinin tamamı, kullanıcının 24/45/47/49 değişiklikleriyle kesinleştirildi. STEP backend, web ve üç OS takip istemcisi kaynakları geliştirildi ve bağımsız kaynak incelemesinden geçti. Test/build/çalışma zamanı ve canlı sağlayıcı doğrulaması yapılmadı; ilk canlı sürüm hazır veya yayımlanmış sayılmaz.

- [Ürün kararları](kararlar.md)
- [52 sorunun karar eşleştirmesi](soru-karar-eslestirmesi.md)
- [Tam ürün kapsamı ve kabul kriterleri](urun-kapsami.md)
- [Geliştirme paketleri ve sırası](gelistirme-plani.md)
- [Upwork referansı ve değerlendirmesi](upwork-karsilastirmasi.md)
- [Uygulama durumu ve M01–M12 kapsam izi](uygulama-durumu.md)
- [Teknik kararlar](teknik-kararlar.md) ve [API sözleşmesi](contracts/api.md)
- [Kurulum ve dağıtım](deployment.md)
- [Backend](backend/README.md), [web](frontend/README.md), [masaüstü takip](desktop/README.md)

## İlk canlı sürüm

Bütün Türkiye üniversitelerinden 18 yaş ve üzeri önlisans/lisans/yüksek lisans/doktora öğrencileri ile Türkiye'deki bireysel/kurumsal işverenleri buluşturur. Yazılım, veri/AI, tasarım, video, çeviri ve içerik başlangıç kategorileridir; öğrenci takımları da iş alabilir.

İlk sürüm mobil uyumlu web, profil/portföy, ilan/başvuru/davet, takım, kredi, sözleşme, ödeme, yazılı mesaj/dosya, değerlendirme, bildirim, yönetim/destek ve Windows/macOS/Linux takip istemcisini kapsar.

## Hesap ve doğrulama

- E-posta/şifre, şifre sıfırlama ve aynı hesapta öğrenci/işveren rolleri.
- Öğrenci doğrulaması yalnız üniversite e-postasıyla; yönetim öğrenci alan adlarını tanımlar. Yıllık yenileme vardır; mezuniyet/erişim kaybında mevcut işler tamamlanabilir, yeni başvurular kapanır.
- Canlı ilan yayımlamada birey için telefon/kimlik, kurum için ayrıca kurum/yetkili doğrulaması.
- İlk ürün testinde e-posta girişi, deneme ödeme ortamı ve yönetimden test kredileri kullanılır. Ek doğrulamalar ürün hazırlandıktan sonraki canlıya hazırlık aşamasındadır.

## Pazar, kredi ve gerçek para

- İlan başlık/açıklama, kategori, beceri, çalışma türü, bütçe ve beklenen süre içerir. Teklif metni/ücret/süreyle başvuru, davet ve bir ilandan ayrı sözleşmelerle çoklu işe alım vardır.
- İlan açma, başvuru ve öne çıkarma kredi kullanır; davete verilen teklif başvuru kredisi harcamaz. İlk maliyetler sabittir; sayısal tutarlar ve sonraki kurallar ayrıca belirlenir.
- Öğrenci/işveren başlangıç ve aylık ücretsiz kredi alabilir, ayrıca satın alabilir. Bütün krediler süresizdir; hesaplar arasında aktarılmaz.
- İlan iptali/moderasyonla kaldırmada ilan/başvuru kredileri iade edilir. Ret, geri çekme veya başvuru süresinin dolması iade doğurmaz. Kaldırılan ilanın kullanılmamış öne çıkarma süresi kredi olarak iade edilir.
- İş bedeli gerçek para ve ilk canlı para birimi TL'dir. Yalnız freelancer iş bedelinden %10 platform komisyonu kesilir.
- Sabit iş aşamaları önceden fonlanır; onay veya 14 günlük yanıtsızlıkla ödenir. Yeniden teslimde süre yeniden başlar; revizyon/itirazda ödeme bekler, anlaşmazlığı destek ekibi inceler.
- Saatlik iş haftalık limit ve ön fonlama kullanır. 5 günlük inceleme/itiraz döneminden sonra ödeme yapılır; manuel süre işverenin açık onayını gerektirir. Kazanç için kendi adına banka hesabına çekim talebi vardır.

## Takım ve takip

Lider takım adına başvurur, sözleşmeyi kabul eder ve kazancı alır. Ayrı takım kredi bakiyesini yönetir. Sözleşmede çalışan üyeler ve ayrı saat ücretleri bulunur; üyeler mesajlaşabilir, teslim yükleyebilir ve kendi sürelerini kaydedebilir. Toplam süre takım limitine sayılır. Aktif lider değişikliği işveren ve yönetim onayı gerektirir; mevcut işin ödeme alıcısının kimliği ayrıca açıkça onaylanır. Ekip içi paylaşımı takım yapar.

Takip saatlikte zorunlu, sabit işte isteğe bağlıdır. Süre/açıklama, her 10 dakikalık bölümde seçili ekrandan rastgele görüntü, etkinlik sayısı ve aktif uygulama bilgisi tutulur. Tuş içeriği/kamera/video kaydı yoktur. Hareketsizlikte duraklama ve çevrimdışı kayıt/senkronizasyon bulunur.

Öğrenci görüntü silemez; kişisel bilgi için işverene gösterilmeden moderasyon talebi açabilir. Talep konusu görüntü inceleme sonuçlanana kadar bütün işveren kanallarında kapalıdır. Görüntü/ayrıntılı etkinlik saklama süresi 90 gündür; açık itirazın ilgili kayıtları sonuçlanana kadar korunur.

## Ürün bağlantıları ve sonraki sürüm

FIRST kullanımı zorunlu değildir; FIRST proje/katkı bağlantılarını portföye ekleme ilk sürümdedir. Otomatik veri aktarımı ve ortak giriş ayrı entegrasyon aşamasındadır; kaynak erişim izinleri taşınmaz.

AI ilan desteği ve INTO üzerinden isteğe bağlı kapsam/teslim incelemesi sonraki sürümdedir. Yerel mobil uygulama, hazır hizmet paketleri, abonelik, sesli/görüntülü görüşme ve öne çıkarma açık artırması da sonraya bırakılmıştır.

Stack, API ve görüntü moderasyonu kaynakları teknik kararlarda tanımlandı. Kredi rakamları, çekim takvimi ve idle/preview politikası yönetimden yapılandırılır. Gerçek sağlayıcı banka çekim kabiliyeti, hesap/anahtarları ve imzalı OS paketleri canlıya hazırlıkta tamamlanmalıdır; ayrıntılar uygulama durumu belgesindedir.

## Geliştirme notu — UI tasarım portföyü

2 Ekim 2026 kullanıcı notu: Freelance bölümünde öğrenciler, Dribbble ve Figma gibi kaynaklardaki UI tasarım çalışmalarını bağlantıyla profil/portföylerine ekleyebilmeli ve STEP içinde gösterebilmelidir. İşverenler bu tasarım örneklerini freelancer'ın portföyünde inceleyebilmelidir.

Bu gereksinim henüz uygulanmış özellik değildir. Önizleme/gömülü gösterim yöntemi ve hangi sürümde ekleneceği uygulama planlamasında netleştirilecektir.
