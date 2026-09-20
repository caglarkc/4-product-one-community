# FIRST — Proje kategorileri ve durumları

Bu başlangıç kataloğu **25 üst kategori, 394 alt kategori ve 6 proje durumu** içerir. Uygulamanın tek yetkili katalog kaynağı [backend/projects/taxonomy.py](backend/projects/taxonomy.py) dosyasıdır; bu belge aynı değerlerin okunabilir tam listesidir.

## Seçim kuralı

- **Üst kategori**, projenin ana çıktısının türünü belirtir: web uygulaması, model, ajan, kütüphane, dokümantasyon gibi.
- **Alt kategori**, seçilen tür içindeki kullanım amacını veya hizmet ettiği alanı belirtir. Alt kategori listesi üst kategoriye özeldir; başka bir üst kategorinin alt seçeneği kullanılamaz.
- **Proje durumu**, projenin bugün bulunduğu aşamadır ve kategoriden ayrı seçilir.
- Her proje için bir üst kategori, ona bağlı bir alt kategori ve bir durum seçilir. Çok amaçlı projede ana çıktı ve baskın amaç esas alınır. Üst kategori değiştiğinde alt kategori yeniden seçilir.
- React, Django, iOS, CNN veya kullanılan model ailesi bu alanların alt kategorisi değildir. Teknoloji bilgileri proje açıklamasında belirtilir.
- Aynı alt kategori kodu farklı üst kategorilerde bulunabilir; anlamını üst ve alt kodun birlikte değerlendirilmesi belirler. En sondaki “Diğer” yalnız ilgili proje türünde listelenmeyen amaçlar içindir.

## Tür sınırları ve örnekler

| Proje | Üst kategori | Alt kategori | Seçim gerekçesi |
|---|---|---|---|
| Hasta randevusu için tarayıcıdan kullanılan uygulama | Web Uygulaması | Sağlık ve Hasta Takibi | Ana çıktı son kullanıcı web uygulamasıdır. |
| Emlak seçeneklerini araştırıp görevleri yürüten ajan | Yapay Zekâ Ajanı | Emlak Araştırma ve Eşleştirme | Ana çıktı hedefe yönelik adımları yürüten ajandır. |
| Tıbbi görüntüler için eğitilen model | Yapay Zekâ Modeli | Sağlık Araştırması ve Klinik Destek | Ana çıktı eğitilen modeldir; çevresindeki arayüz ikincildir. |
| Kullanıcının başlattığı belge inceleme aracı | Yapay Zekâ Destekli Araç | Belge Okuma ve Bilgi Çıkarma | Ana çıktı belirli bir işi destekleyen araçtır. |
| Sipariş yaşam döngüsünü yöneten servisler bütünü | Backend Sistemi | Sipariş ve Ticaret Operasyonları | Ana çıktı uygulamanın iş kurallarını ve durumunu yönetir. |
| Diğer uygulamalara ürün fiyatı sağlayan servis | API Servisi | Ürün, Fiyat ve Stok Verileri | Ana çıktı dış tüketicilere sunulan veri veya işlem arayüzüdür. |
| Kod incelemesi yapan ajan için tekrar kullanılabilir talimat paketi | Skill Dosyaları ve Ajan Talimatları | Kod İnceleme ve Kalite | Ana çıktı ajan talimat dosyalarıdır; çalışan ajan değildir. |
| Açık kaynak projeye katılım rehberi | Dokümantasyon ve Bilgi Kaynağı | Katkı ve Topluluk Rehberleri | Ana çıktı okunabilir rehber ve bilgi kaynağıdır. |
| Sağlık ürünleri için ortak form ve bileşen seti | UI Bileşen ve Tasarım Sistemi | Sağlık ve Bakım Arayüzleri | Ana çıktı tekrar kullanılabilir arayüz sistemidir. |

Bir projenin AI, güvenlik veya veri özelliği içermesi tek başına üst kategoriyi belirlemez. Ana çıktı özel amaçlı bir güvenlik ürünü ise “Siber Güvenlik Aracı”; paylaşılan veri altyapısı ise “Veri Platformu”; üretim biçimi ajan/model/skill ise ilgili tür seçilir. Birden fazla türün eşit derecede uygun olduğu projede sahibi, katkı aradığı ana çıktıyı esas alır.

Skill ve dokümantasyon projelerinde “yayın”, paketin veya belgenin erişime açılmasını da kapsar. Durumlar proje sahibinin beyanıdır; otomatik test sonucu, teknik kalite garantisi ya da zorunlu yayın kapısı değildir.

## Proje durumları

| Kod | Görünen ad | Açıklama |
|---|---|---|
| `idea` | Fikir ve Planlama | Amaç, kapsam ve ihtiyaçlar netleştiriliyor; uygulama henüz başlamamış olabilir. |
| `prototype` | İlk Prototip | İlk çalışan örnek veya başlangıç çıktıları hazırlanıyor; temel yaklaşım deneniyor. |
| `development` | Aktif Geliştirme | Temel özellikler ve içerikler geliştiriliyor; proje kapsamı adım adım tamamlanıyor. |
| `release-preparation` | Yayına Hazırlık | İlk yayının kapsamı toparlanıyor; dağıtım, kullanım ve sunum hazırlıkları yapılıyor. |
| `pre-release-testing` | Yayın Öncesi Test | Yayın adayı son kontrollerden geçiyor; hatalar ve eksikler gideriliyor. |
| `live-development` | Yayında ve Geliştiriliyor | Proje kullanıma veya erişime açıldı; iyileştirme ve yeni özellik çalışmaları sürüyor. |

## Tam kategori listesi

### 1. Web Uygulaması

Üst kategori kodu: `web-app`. Alt kategori sayısı: 25.

| Alt kategori kodu | Görünen ad |
|---|---|
| `health` | Sağlık ve Hasta Takibi |
| `education` | Eğitim ve Öğrenme |
| `finance` | Finans ve Bütçe |
| `real-estate` | Emlak ve Mülk Yönetimi |
| `commerce` | E-ticaret ve Mağazacılık |
| `marketplace` | Pazar Yeri ve Hizmet Eşleştirme |
| `community` | Topluluk ve Sosyal Ağ |
| `collaboration` | Ekip Çalışması ve Proje Yönetimi |
| `productivity` | Kişisel Üretkenlik |
| `content-publishing` | İçerik ve Yayıncılık |
| `recruitment` | İş ve Yetenek Eşleştirme |
| `customer-relations` | Müşteri İlişkileri |
| `booking` | Randevu ve Rezervasyon |
| `events` | Etkinlik ve Biletleme |
| `travel` | Seyahat ve Turizm |
| `logistics` | Lojistik ve Teslimat |
| `food` | Yemek ve Restoran Yönetimi |
| `agriculture` | Tarım ve Gıda Sistemleri |
| `sustainability` | Çevre ve Sürdürülebilirlik |
| `civic-services` | Kamusal Hizmetler ve Sivil Katılım |
| `accessibility` | Erişilebilirlik ve Kapsayıcılık |
| `legal` | Hukuk ve Uyum |
| `security` | Güvenlik ve Risk Yönetimi |
| `entertainment` | Medya ve Eğlence |
| `other-web` | Diğer Web Uygulamaları |

### 2. Mobil Uygulama

Üst kategori kodu: `mobile-app`. Alt kategori sayısı: 23.

| Alt kategori kodu | Görünen ad |
|---|---|
| `personal-health` | Kişisel Sağlık Takibi |
| `mental-wellbeing` | Ruh Sağlığı ve İyi Oluş |
| `fitness` | Spor ve Egzersiz |
| `nutrition` | Beslenme ve Yemek Planlama |
| `learning` | Mobil Öğrenme |
| `language-learning` | Dil Öğrenme |
| `personal-finance` | Kişisel Finans |
| `shopping` | Alışveriş ve Sadakat |
| `social` | Sosyal İletişim ve Topluluk |
| `local-discovery` | Yerel Mekân ve Hizmet Keşfi |
| `travel` | Seyahat Planlama |
| `navigation` | Navigasyon ve Ulaşım |
| `field-work` | Saha Çalışması ve Ekip Yönetimi |
| `home-management` | Ev ve Yaşam Yönetimi |
| `caregiving` | Aile ve Bakım Desteği |
| `accessibility` | Erişilebilirlik Desteği |
| `personal-safety` | Kişisel Güvenlik ve Acil Durum |
| `habits` | Alışkanlık ve Günlük Planlama |
| `creativity` | Fotoğraf, Ses ve Yaratıcı Üretim |
| `events` | Etkinlik ve Sosyal Buluşma |
| `agriculture` | Çiftçi ve Tarla Desteği |
| `property` | Emlak Arama ve Mülk Takibi |
| `other-mobile` | Diğer Mobil Uygulamalar |

### 3. Masaüstü Uygulaması

Üst kategori kodu: `desktop-app`. Alt kategori sayısı: 15.

| Alt kategori kodu | Görünen ad |
|---|---|
| `document-work` | Belge ve Ofis Çalışması |
| `creative-design` | Görsel Tasarım ve İllüstrasyon |
| `video-production` | Video Üretimi ve Kurgu |
| `audio-production` | Ses ve Müzik Üretimi |
| `engineering-design` | Mühendislik ve Teknik Çizim |
| `research-analysis` | Araştırma ve Veri Analizi |
| `software-work` | Yazılım Geliştirme Desteği |
| `file-management` | Dosya ve Arşiv Yönetimi |
| `knowledge-management` | Not ve Bilgi Yönetimi |
| `communication` | İletişim ve Toplantı |
| `business-operations` | İşletme Operasyonları |
| `accessibility` | Masaüstü Erişilebilirliği |
| `privacy-security` | Gizlilik ve Cihaz Güvenliği |
| `education` | Eğitim ve Sınıf Çalışması |
| `other-desktop` | Diğer Masaüstü Uygulamaları |

### 4. Yapay Zekâ Ajanı

Üst kategori kodu: `ai-agent`. Alt kategori sayısı: 24.

| Alt kategori kodu | Görünen ad |
|---|---|
| `research` | Araştırma ve Kaynak Tarama |
| `coding` | Kod Geliştirme ve Bakım |
| `software-quality` | Yazılım İnceleme ve Kalite |
| `cyber-defense` | Siber Savunma ve Olay Analizi |
| `customer-support` | Müşteri Destek Operasyonları |
| `sales` | Satış ve Müşteri Takibi |
| `marketing` | Pazarlama ve Kampanya Yönetimi |
| `content-operations` | İçerik Üretimi ve Yayın Akışı |
| `personal-assistant` | Kişisel Asistanlık ve Planlama |
| `learning-coach` | Öğrenme ve Eğitim Koçluğu |
| `health-support` | Sağlık Bilgilendirme ve Bakım Desteği |
| `finance-analysis` | Finansal Araştırma ve Analiz |
| `legal-research` | Hukuki Araştırma ve Belge İnceleme |
| `real-estate` | Emlak Araştırma ve Eşleştirme |
| `recruitment` | İşe Alım ve Aday Eşleştirme |
| `project-coordination` | Proje ve Ekip Koordinasyonu |
| `business-operations` | İş Süreci Operasyonları |
| `data-analysis` | Veri Analizi ve Raporlama |
| `it-operations` | BT Operasyonları ve Sorun Giderme |
| `commerce` | Alışveriş ve Ticaret Desteği |
| `travel-planning` | Seyahat ve Rezervasyon Planlama |
| `accessibility` | Erişilebilirlik ve Günlük Yaşam Desteği |
| `scientific-discovery` | Bilimsel Araştırma Desteği |
| `other-agent` | Diğer Yapay Zekâ Ajanları |

### 5. Yapay Zekâ Modeli

Üst kategori kodu: `ai-model`. Alt kategori sayısı: 23.

| Alt kategori kodu | Görünen ad |
|---|---|
| `health` | Sağlık Araştırması ve Klinik Destek |
| `biomedicine` | Biyomedikal ve İlaç Araştırması |
| `cybersecurity` | Siber Tehdit ve Anomali Tespiti |
| `fraud-detection` | Dolandırıcılık ve Kötüye Kullanım Tespiti |
| `financial-risk` | Finansal Risk ve Öngörü |
| `language-access` | Çeviri ve Dil Erişimi |
| `accessibility` | Engelsiz İletişim ve Erişilebilirlik |
| `education` | Öğrenme ve Eğitim Değerlendirmesi |
| `scientific-research` | Bilimsel Keşif ve Araştırma |
| `climate` | İklim ve Çevre Analizi |
| `agriculture` | Tarım ve Bitki Sağlığı |
| `industrial-quality` | Üretim Kalitesi ve Hata Tespiti |
| `predictive-maintenance` | Arıza Öngörüsü ve Bakım |
| `transport` | Trafik ve Ulaşım Analizi |
| `energy` | Enerji Talebi ve Verimlilik |
| `real-estate` | Gayrimenkul Değerleme ve Analizi |
| `commerce` | Talep Tahmini ve Ticaret Analizi |
| `recommendations` | İçerik ve Ürün Önerileri |
| `content-safety` | İçerik Güvenliği ve Moderasyon |
| `creative-production` | Yaratıcı İçerik Üretimi |
| `software-assistance` | Kodlama ve Yazılım Anlama |
| `search-knowledge` | Bilgi Arama ve Anlamlandırma |
| `other-model` | Diğer Yapay Zekâ Modelleri |

### 6. Yapay Zekâ Destekli Araç

Üst kategori kodu: `ai-tool`. Alt kategori sayısı: 20.

| Alt kategori kodu | Görünen ad |
|---|---|
| `writing` | Yazı ve Editörlük |
| `visual-creation` | Görsel Üretim ve Düzenleme |
| `video-creation` | Video Üretimi ve Düzenleme |
| `audio-creation` | Ses ve Müzik Çalışmaları |
| `meeting-assistance` | Toplantı ve Görüşme Desteği |
| `translation` | Çeviri ve Yerelleştirme |
| `coding-assistance` | Kodlama ve Hata Giderme |
| `research-assistance` | Araştırma ve Kaynak Değerlendirme |
| `document-analysis` | Belge Okuma ve Bilgi Çıkarma |
| `data-insights` | Veri Analizi ve İçgörü |
| `learning-assistance` | Ders Çalışma ve Öğrenme |
| `accessibility` | Erişilebilir İçerik ve İletişim |
| `health-information` | Sağlık Bilgilendirme |
| `legal-assistance` | Hukuki Belge ve Araştırma Desteği |
| `finance-assistance` | Finansal Analiz Desteği |
| `real-estate` | Emlak İnceleme ve Sunum |
| `marketing-assistance` | Pazarlama ve Marka İçeriği |
| `security-assistance` | Güvenlik Analizi Desteği |
| `career-assistance` | Kariyer ve Başvuru Desteği |
| `other-ai-tool` | Diğer Yapay Zekâ Araçları |

### 7. Backend Sistemi

Üst kategori kodu: `backend-system`. Alt kategori sayısı: 17.

| Alt kategori kodu | Görünen ad |
|---|---|
| `identity-access` | Kimlik ve Erişim Yönetimi |
| `commerce-operations` | Sipariş ve Ticaret Operasyonları |
| `payments-billing` | Ödeme ve Faturalandırma |
| `inventory` | Stok ve Tedarik Yönetimi |
| `logistics` | Lojistik ve Sevkiyat Yönetimi |
| `booking` | Randevu ve Rezervasyon Yönetimi |
| `communication` | Mesajlaşma ve Bildirim |
| `content-management` | İçerik ve Medya Yönetimi |
| `community-management` | Topluluk ve Üyelik Yönetimi |
| `learning-management` | Eğitim ve Öğrenme Yönetimi |
| `health-records` | Sağlık ve Bakım Kayıtları |
| `financial-records` | Finans ve Muhasebe Kayıtları |
| `property-management` | Mülk ve Kiralama Yönetimi |
| `workflow-management` | İş Akışı ve Süreç Yönetimi |
| `compliance-audit` | Uyum ve Denetim Kayıtları |
| `public-services` | Kamu ve Belediye Hizmetleri |
| `other-backend` | Diğer Backend Sistemleri |

### 8. API Servisi

Üst kategori kodu: `api-service`. Alt kategori sayısı: 16.

| Alt kategori kodu | Görünen ad |
|---|---|
| `identity-verification` | Kimlik ve Hesap Doğrulama |
| `payments` | Ödeme ve Finans İşlemleri |
| `messaging` | Mesaj ve Bildirim İletimi |
| `maps-location` | Harita ve Konum Hizmetleri |
| `weather-climate` | Hava Durumu ve İklim Verileri |
| `transport-logistics` | Ulaşım ve Lojistik Verileri |
| `health-data` | Sağlık Verisi Entegrasyonu |
| `education-data` | Eğitim Verisi Entegrasyonu |
| `commerce-data` | Ürün, Fiyat ve Stok Verileri |
| `property-data` | Emlak ve Adres Verileri |
| `public-data` | Açık Veri ve Kamusal Veriler |
| `search-discovery` | Arama ve Bilgi Keşfi |
| `media-processing` | Medya İşleme ve Dağıtımı |
| `language-services` | Dil ve Çeviri Hizmetleri |
| `risk-intelligence` | Güvenlik ve Risk İstihbaratı |
| `other-api` | Diğer API Servisleri |

### 9. Kütüphane ve SDK

Üst kategori kodu: `library-sdk`. Alt kategori sayısı: 15.

| Alt kategori kodu | Görünen ad |
|---|---|
| `identity-security` | Kimlik ve Güvenlik Entegrasyonu |
| `payment-integration` | Ödeme ve Ticaret Entegrasyonu |
| `data-processing` | Veri İşleme ve Dönüştürme |
| `data-visualization` | Veri Görselleştirme |
| `scientific-analysis` | Bilimsel ve Sayısal Analiz |
| `media-processing` | Görüntü, Ses ve Video İşleme |
| `language-processing` | Dil ve Metin İşleme |
| `accessibility` | Erişilebilirlik Geliştirme |
| `localization` | Çeviri ve Yerelleştirme |
| `maps-geospatial` | Harita ve Coğrafi Analiz |
| `developer-productivity` | Geliştirici Üretkenliği |
| `quality-assurance` | Yazılım Kalitesi ve Doğrulama |
| `observability` | Sistem İzleme ve Hata Analizi |
| `device-integration` | Cihaz ve Donanım Entegrasyonu |
| `other-library` | Diğer Kütüphane ve SDK'lar |

### 10. Komut Satırı Aracı

Üst kategori kodu: `cli-tool`. Alt kategori sayısı: 14.

| Alt kategori kodu | Görünen ad |
|---|---|
| `project-setup` | Proje Kurulumu ve İskelet Oluşturma |
| `code-maintenance` | Kod Düzenleme ve Bakım |
| `release-management` | Sürüm ve Yayın Yönetimi |
| `infrastructure-management` | Altyapı ve Ortam Yönetimi |
| `data-conversion` | Veri Dönüştürme ve Aktarma |
| `database-operations` | Veritabanı Yönetimi |
| `file-operations` | Dosya ve Arşiv İşlemleri |
| `backup-recovery` | Yedekleme ve Kurtarma |
| `security-audit` | Güvenlik Denetimi |
| `network-diagnostics` | Ağ Analizi ve Sorun Giderme |
| `media-operations` | Medya İşleme |
| `research-workflows` | Araştırma İş Akışları |
| `personal-productivity` | Kişisel Üretkenlik |
| `other-cli` | Diğer Komut Satırı Araçları |

### 11. Tarayıcı Eklentisi

Üst kategori kodu: `browser-extension`. Alt kategori sayısı: 13.

| Alt kategori kodu | Görünen ad |
|---|---|
| `privacy-protection` | Gizlilik ve Takip Koruması |
| `browsing-security` | Güvenli Gezinme |
| `accessibility` | Web Erişilebilirliği |
| `reading-research` | Okuma ve Araştırma |
| `translation` | Çeviri ve Dil Desteği |
| `writing-assistance` | Yazma ve Metin Desteği |
| `productivity-focus` | Üretkenlik ve Odaklanma |
| `bookmark-knowledge` | Yer İmi ve Bilgi Yönetimi |
| `shopping-comparison` | Alışveriş ve Fiyat Karşılaştırma |
| `web-development` | Web Geliştirme ve İnceleme |
| `content-management` | İçerik Kaydetme ve Düzenleme |
| `learning` | Öğrenme ve Ders Çalışma |
| `other-extension` | Diğer Tarayıcı Eklentileri |

### 12. Otomasyon ve İş Akışı

Üst kategori kodu: `automation-workflow`. Alt kategori sayısı: 15.

| Alt kategori kodu | Görünen ad |
|---|---|
| `sales-operations` | Satış ve Müşteri Operasyonları |
| `marketing-operations` | Pazarlama ve Kampanya Akışları |
| `support-operations` | Müşteri Destek Akışları |
| `finance-operations` | Finans ve Muhasebe Akışları |
| `hr-operations` | İnsan Kaynakları ve İşe Alım |
| `commerce-operations` | Ticaret ve Sipariş Akışları |
| `content-publishing` | İçerik Hazırlama ve Yayınlama |
| `document-processing` | Belge İşleme ve Onay |
| `research-collection` | Araştırma ve Bilgi Toplama |
| `data-synchronization` | Veri Aktarımı ve Eşitleme |
| `it-maintenance` | BT Bakım ve Operasyonları |
| `security-response` | Güvenlik Uyarısı ve Müdahale |
| `personal-productivity` | Kişisel Görev ve Hatırlatmalar |
| `community-operations` | Topluluk ve Etkinlik Operasyonları |
| `other-automation` | Diğer Otomasyon Akışları |

### 13. Veri Platformu

Üst kategori kodu: `data-platform`. Alt kategori sayısı: 15.

| Alt kategori kodu | Görünen ad |
|---|---|
| `public-data` | Açık Veri ve Kamusal Bilgi |
| `health-research` | Sağlık ve Klinik Araştırma Verileri |
| `finance-analytics` | Finans ve Ekonomi Analitiği |
| `commerce-analytics` | Ticaret ve Müşteri Analitiği |
| `education-analytics` | Eğitim ve Öğrenme Analitiği |
| `climate-environment` | İklim ve Çevre Verileri |
| `agriculture-food` | Tarım ve Gıda Verileri |
| `geospatial` | Coğrafi Bilgi ve Kent Analitiği |
| `transport-logistics` | Ulaşım ve Lojistik Analitiği |
| `industrial-analytics` | Üretim ve Bakım Analitiği |
| `energy-analytics` | Enerji ve Kaynak Analitiği |
| `security-analytics` | Güvenlik ve Tehdit Verileri |
| `research-data` | Bilimsel Veri Paylaşımı |
| `organizational-knowledge` | Kurumsal Bilgi ve Veri Yönetimi |
| `other-data` | Diğer Veri Platformları |

### 14. DevOps ve Altyapı Platformu

Üst kategori kodu: `devops-platform`. Alt kategori sayısı: 13.

| Alt kategori kodu | Görünen ad |
|---|---|
| `release-delivery` | Yazılım Yayınlama ve Teslim |
| `environment-management` | Geliştirme ve Çalışma Ortamları |
| `infrastructure-provisioning` | Altyapı Kurulumu ve Yönetimi |
| `service-reliability` | Hizmet Sürekliliği ve Güvenilirlik |
| `system-observability` | Sistem Gözlemi ve Sorun Analizi |
| `incident-management` | Operasyonel Olay Yönetimi |
| `cloud-cost` | Bulut Maliyeti ve Kaynak Verimliliği |
| `backup-recovery` | Yedekleme ve Felaket Kurtarma |
| `secrets-access` | Gizli Bilgi ve Altyapı Erişimi |
| `supply-chain-security` | Yazılım Tedarik Zinciri Güvenliği |
| `compliance-reporting` | Altyapı Uyumu ve Denetim |
| `team-self-service` | Geliştirici Platformu ve Self Servis |
| `other-devops` | Diğer DevOps Platformları |

### 15. Siber Güvenlik Aracı

Üst kategori kodu: `cybersecurity-tool`. Alt kategori sayısı: 15.

| Alt kategori kodu | Görünen ad |
|---|---|
| `application-security` | Uygulama Güvenliği |
| `network-defense` | Ağ Güvenliği ve Savunması |
| `endpoint-protection` | Cihaz ve Uç Nokta Koruması |
| `cloud-security` | Bulut Güvenliği |
| `identity-security` | Kimlik ve Erişim Güvenliği |
| `vulnerability-management` | Zafiyet Yönetimi |
| `threat-intelligence` | Tehdit İstihbaratı |
| `incident-response` | Olay Müdahalesi |
| `forensics` | Dijital Adli Analiz |
| `phishing-defense` | Kimlik Avı ve Dolandırıcılık Koruması |
| `data-protection` | Veri Güvenliği ve Gizlilik |
| `security-awareness` | Güvenlik Eğitimi ve Farkındalık |
| `security-validation` | Yetkili Güvenlik Değerlendirmesi |
| `compliance-risk` | Güvenlik Uyumu ve Risk Yönetimi |
| `other-security` | Diğer Siber Güvenlik Araçları |

### 16. Nesnelerin İnterneti Sistemi

Üst kategori kodu: `iot-system`. Alt kategori sayısı: 13.

| Alt kategori kodu | Görünen ad |
|---|---|
| `smart-home` | Akıllı Ev ve Yaşam Alanları |
| `smart-building` | Bina ve Tesis Yönetimi |
| `health-monitoring` | Uzaktan Sağlık ve Bakım Takibi |
| `agriculture-monitoring` | Tarım ve Sulama Takibi |
| `industrial-monitoring` | Üretim ve Makine İzleme |
| `energy-management` | Enerji ve Tüketim Yönetimi |
| `environment-monitoring` | Hava, Su ve Çevre İzleme |
| `asset-tracking` | Varlık ve Envanter Takibi |
| `transport-fleet` | Ulaşım ve Filo Takibi |
| `cold-chain` | Soğuk Zincir ve Gıda Güvenliği |
| `urban-services` | Kent Altyapısı ve Hizmetleri |
| `disaster-monitoring` | Afet ve Erken Uyarı |
| `other-iot` | Diğer IoT Sistemleri |

### 17. Gömülü Sistem

Üst kategori kodu: `embedded-system`. Alt kategori sayısı: 12.

| Alt kategori kodu | Görünen ad |
|---|---|
| `medical-devices` | Sağlık ve Yardımcı Cihazlar |
| `assistive-devices` | Erişilebilirlik ve Destek Cihazları |
| `industrial-control` | Endüstriyel Kontrol |
| `vehicle-systems` | Araç ve Ulaşım Sistemleri |
| `energy-control` | Enerji ve Güç Yönetimi |
| `consumer-devices` | Günlük Yaşam ve Tüketici Cihazları |
| `measurement` | Ölçüm ve Veri Toplama |
| `communication-devices` | Haberleşme Cihazları |
| `agriculture-control` | Tarım ve Sulama Kontrolü |
| `safety-systems` | Emniyet ve Alarm Sistemleri |
| `education-kits` | Eğitim ve Deney Setleri |
| `other-embedded` | Diğer Gömülü Sistemler |

### 18. Robotik

Üst kategori kodu: `robotics`. Alt kategori sayısı: 12.

| Alt kategori kodu | Görünen ad |
|---|---|
| `industrial-production` | Üretim ve Montaj |
| `warehouse-logistics` | Depo ve Lojistik |
| `health-rehabilitation` | Sağlık ve Rehabilitasyon |
| `assistive-care` | Bakım ve Günlük Yaşam Desteği |
| `agriculture` | Tarım ve Hasat |
| `inspection-maintenance` | İnceleme ve Bakım |
| `search-rescue` | Arama ve Kurtarma |
| `education` | Robotik Eğitimi |
| `research-exploration` | Araştırma ve Keşif |
| `home-services` | Ev ve Tesis Hizmetleri |
| `environment-restoration` | Çevre İzleme ve İyileştirme |
| `other-robotics` | Diğer Robotik Projeleri |

### 19. Oyun

Üst kategori kodu: `game`. Alt kategori sayısı: 13.

| Alt kategori kodu | Görünen ad |
|---|---|
| `entertainment` | Eğlence ve Serbest Oyun |
| `education` | Eğitim ve Kavram Öğrenme |
| `language-learning` | Dil Öğrenme ve Pratik |
| `health-rehabilitation` | Sağlık ve Rehabilitasyon |
| `cognitive-training` | Bilişsel Beceri ve Hafıza |
| `professional-training` | Mesleki Eğitim ve Simülasyon |
| `social-cooperation` | Sosyal Etkileşim ve İş Birliği |
| `culture-history` | Kültür, Tarih ve Miras |
| `science-exploration` | Bilim ve Keşif |
| `civic-awareness` | Toplumsal Farkındalık |
| `accessibility` | Erişilebilir Oyun Deneyimi |
| `creative-expression` | Yaratıcılık ve Anlatı |
| `other-game` | Diğer Oyun Amaçları |

### 20. XR / AR / VR Uygulaması

Üst kategori kodu: `xr-app`. Alt kategori sayısı: 13.

| Alt kategori kodu | Görünen ad |
|---|---|
| `immersive-learning` | Deneyimsel Eğitim |
| `professional-training` | Mesleki Eğitim ve Güvenlik |
| `health-rehabilitation` | Sağlık ve Rehabilitasyon |
| `architecture-property` | Mimari ve Emlak Deneyimi |
| `industrial-assistance` | Üretim ve Bakım Desteği |
| `remote-collaboration` | Uzaktan İş Birliği |
| `culture-heritage` | Kültür ve Miras Keşfi |
| `retail-experience` | Alışveriş ve Ürün Deneyimi |
| `entertainment` | Eğlence ve Etkileşimli Deneyim |
| `scientific-visualization` | Bilimsel Görselleştirme |
| `accessibility` | Erişilebilirlik ve Yardımcı Deneyimler |
| `tourism` | Seyahat ve Mekân Keşfi |
| `other-xr` | Diğer XR Uygulamaları |

### 21. Blokzincir Uygulaması

Üst kategori kodu: `blockchain-app`. Alt kategori sayısı: 12.

| Alt kategori kodu | Görünen ad |
|---|---|
| `identity-credentials` | Kimlik ve Doğrulanabilir Belgeler |
| `payment-transfer` | Ödeme ve Değer Transferi |
| `financial-services` | Finansal Hizmetler |
| `supply-chain` | Tedarik Zinciri ve İzlenebilirlik |
| `ownership-rights` | Mülkiyet ve Hak Yönetimi |
| `community-governance` | Topluluk Yönetimi ve Katılım |
| `public-transparency` | Kamusal Şeffaflık ve Hesap Verebilirlik |
| `creator-economy` | Üretici ve İçerik Ekonomisi |
| `research-integrity` | Araştırma Kaydı ve Bütünlüğü |
| `environment-markets` | Çevre ve Kaynak Takibi |
| `charity-funding` | Bağış ve Topluluk Finansmanı |
| `other-blockchain` | Diğer Blokzincir Uygulamaları |

### 22. Bilimsel Hesaplama

Üst kategori kodu: `scientific-computing`. Alt kategori sayısı: 13.

| Alt kategori kodu | Görünen ad |
|---|---|
| `bioinformatics` | Biyoinformatik ve Genom Araştırması |
| `drug-discovery` | İlaç ve Molekül Araştırması |
| `physics` | Fizik ve Evren Araştırması |
| `chemistry` | Kimya ve Malzeme Araştırması |
| `climate-modeling` | İklim ve Meteoroloji |
| `geoscience` | Yer Bilimleri ve Afet Analizi |
| `engineering-simulation` | Mühendislik Tasarımı ve Simülasyon |
| `energy-research` | Enerji Sistemleri Araştırması |
| `math-research` | Matematik ve İstatistik Araştırması |
| `social-research` | Sosyal Bilimler ve Ekonomi |
| `neuroscience` | Sinirbilim ve Biliş Araştırması |
| `ecology` | Ekoloji ve Biyoçeşitlilik |
| `other-scientific` | Diğer Bilimsel Hesaplama Projeleri |

### 23. Skill Dosyaları ve Ajan Talimatları

Üst kategori kodu: `skill-files`. Alt kategori sayısı: 16.

| Alt kategori kodu | Görünen ad |
|---|---|
| `software-development` | Yazılım Geliştirme |
| `code-review` | Kod İnceleme ve Kalite |
| `security-review` | Güvenlik İncelemesi |
| `infrastructure-operations` | Altyapı ve Yayın Operasyonları |
| `research-synthesis` | Araştırma ve Bilgi Sentezi |
| `data-analysis` | Veri Analizi ve Raporlama |
| `writing-editing` | Yazı ve Editörlük |
| `product-design` | Ürün ve Deneyim Tasarımı |
| `marketing-content` | Pazarlama ve Marka İçeriği |
| `education-coaching` | Eğitim ve Öğrenme Desteği |
| `document-production` | Belge ve Sunum Hazırlama |
| `project-management` | Proje ve Görev Yönetimi |
| `customer-support` | Müşteri Destek Süreçleri |
| `legal-compliance` | Hukuki Araştırma ve Uyum |
| `accessibility-review` | Erişilebilirlik İncelemesi |
| `other-skills` | Diğer Skill Dosyaları |

### 24. Dokümantasyon ve Bilgi Kaynağı

Üst kategori kodu: `documentation`. Alt kategori sayısı: 14.

| Alt kategori kodu | Görünen ad |
|---|---|
| `getting-started` | Başlangıç ve Kullanım Rehberleri |
| `developer-integration` | Geliştirici ve Entegrasyon Rehberleri |
| `architecture-decisions` | Mimari ve Karar Kayıtları |
| `operations-runbooks` | İşletim ve Sorun Giderme Rehberleri |
| `security-guidance` | Güvenlik ve Gizlilik Rehberleri |
| `contribution-governance` | Katkı ve Topluluk Rehberleri |
| `learning-materials` | Eğitim ve Öğrenme Kaynakları |
| `research-methods` | Araştırma ve Yöntem Belgeleri |
| `data-reference` | Veri Sözlükleri ve Başvuru Kaynakları |
| `accessibility-guidance` | Erişilebilirlik Rehberleri |
| `localization-guidance` | Çeviri ve Yerelleştirme Kaynakları |
| `compliance-guidance` | Standart ve Uyum Rehberleri |
| `product-knowledge` | Ürün ve Alan Bilgisi |
| `other-documentation` | Diğer Dokümantasyon Kaynakları |

### 25. UI Bileşen ve Tasarım Sistemi

Üst kategori kodu: `ui-component-system`. Alt kategori sayısı: 13.

| Alt kategori kodu | Görünen ad |
|---|---|
| `accessible-interfaces` | Erişilebilir Arayüzler |
| `business-workflows` | İşletme ve Yönetim Arayüzleri |
| `commerce-experience` | Alışveriş ve Ticaret Arayüzleri |
| `learning-experience` | Eğitim ve Öğrenme Arayüzleri |
| `health-experience` | Sağlık ve Bakım Arayüzleri |
| `finance-experience` | Finans ve Analiz Arayüzleri |
| `data-exploration` | Veri Keşfi ve Görselleştirme |
| `content-experience` | İçerik ve Yayın Arayüzleri |
| `community-experience` | Topluluk ve İletişim Arayüzleri |
| `maps-navigation` | Harita ve Konum Arayüzleri |
| `public-services` | Kamusal Hizmet Arayüzleri |
| `cross-product-consistency` | Ürünler Arası Görsel Tutarlılık |
| `other-ui-system` | Diğer UI Bileşen Sistemleri |
