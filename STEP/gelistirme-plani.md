# STEP — Geliştirme planı

Tarih: 30 Eylül 2026 (Europe/Istanbul). Bu plan [52 kabul edilmiş kararı](soru-karar-eslestirmesi.md) ve [tam ürün kapsamını](urun-kapsami.md) bağımlılıkları belli geliştirme paketlerine ayırır. Kapsam kaynağı [kararlar.md](kararlar.md) dosyasıdır. Backend/web/masaüstü kaynakları geliştirildi; modül kanıtları [uygulama durumu](uygulama-durumu.md) belgesindedir. Test, build, çalışma zamanı veya yayın doğrulanmadı; dış canlı kapıları ayrı kalır.

İlk canlı sürüm P0–P9'un birlikte tamamlanmasıdır. Paketler geliştirme sırasıdır; saatlik işin, takımın veya üç OS takip istemcisinin ilk canlı sürümden çıkarılması anlamına gelmez. Test aşaması e-posta/şifre, deneme ödemeleri ve test kredileriyle yürür; ek doğrulamalar ürün hazırlandıktan sonra canlıya hazırlıkta etkinleştirilir.

## 1. Paket grafiği ve dosya sahipliği

| Paket | Ön koşul | Tek writer'ın sorumluluk alanı | Çıktı |
|---|---|---|---|
| P0 — Teknik keşif ve sözleşmeler | Kabul edilmiş ürün belgeleri | STEP teknik kararları, API/veri/rol/işlem sözleşmeleri | Uygulanabilir stack, sağlayıcı ve modül sınırları; gerçek uygulama dizinleri |
| P1 — Hesap ve profil | P0 | Hesap, profil, öğrenci/işveren rolü, genel/özel görünürlük | E-posta/şifre, sıfırlama, profil, mobil uyumlu genel keşif temeli |
| P2 — Yönetim ve işlem temeli | P0, P1 | Yönetim yetkileri, kategori/üniversite yapılandırması, işlem ve zamanlı iş altyapısı | Operatör alanları ve tekrar denemeye dayanıklı işlem kayıtları |
| P3 — Kredi ve ilan pazarı | P1, P2 | Kredi bakiyesi/işlemleri, ilan, teklif, davet, öne çıkarma | Pazarın ilan/başvuru ve kredi ekonomisi |
| P4 — Sözleşme ve iletişim | P1, P3 | Sözleşme/kabul/değişiklik, mesaj/dosya, değerlendirme/bildirim | Tarafların anlaşma ve iletişim çalışma alanları |
| P5 — Takım çalışma modeli | P1–P4 | Takım üyeliği/çalışan listesi, lider yetkisi, takım kredi hesabı ve değişiklikleri | Takımın teklif, sözleşme ve çalışma yetkileri |
| P6 — Para ve sabit iş | P2, P4, P5 | Fonlama, komisyon, aşama teslimi/onayı, uyuşmazlık/iade/çekim | Test ortamında sabit işin para yaşam döngüsü |
| P7 — Tracker ve görüntü moderasyonu | P0, P1, P2, P4, P5 | Masaüstü kayıt/senkronizasyon, çalışma günlüğü, görüntü erişimi/moderasyonu/saklaması | Windows/macOS/Linux istemcileri ve gizlilik akışı |
| P8 — Saatlik hesap ve ödeme | P5, P6, P7 | Haftalık fon/saat limitleri, üye ücretleri, manuel süre ve inceleme dönemi | Takip kayıtlarından saatlik kazanç hesabı |
| P9 — Çekirdeğin tamamlanması ve canlı hazırlık | P1–P8 | Modül entegrasyonu, FIRST portföy bağlantıları, canlı doğrulama ve operasyon | İlk canlı kapsamın bütünleştirilmiş teslimi |

Gerçek uygulama dizinleri `STEP/backend`, `STEP/frontend`, `STEP/desktop`; ortak sözleşmeler `STEP/contracts`, dağıtım `STEP/compose.yaml` ve `STEP/deploy` altındadır. Dosya sahipliği, bağımlılık, revizyonlar ve bağımsız source kabul kanıtları `.orchestrator/runs/step-full-development/` içinde korunur.

Ortak sözleşme ve ortak dosyaların tek writer'ı vardır. Sözleşmeler kabul edilmeden farklı tüketicilere paralel yazım verilmez. Bağımlılığı bitmiş, dosya kapsamları ayrılmış işler native alt agentlara devredilebilir; sabit ürün başına agent kadrosu kurulmaz. Bağımsız review/verify kaynak/diff incelemesi yapar. Auth/yetki/API/ödeme/veri saklama işlerinde gerekli kalite kapıları ve ürünler arası integration düğümü korunur.

## 2. P0 — Teknik keşif ve sözleşmeler

- FIRST'ün seçilmiş stack'i ve gerçek kaynakları yeniden kullanım adayı olarak incelenir; STEP için kendiliğinden teknoloji kararı yapılmaz. STEP web/backend ve üç OS masaüstü istemcisi ayrı sorumluluklardır.
- TL iş bedeli, aşama ve haftalık ön fonlama, bekletme/serbest bırakma, iade, %10 komisyon ve kendi adına banka hesabına çekim gereksinimlerini karşılayacak sağlayıcılar resmî güncel kaynaklarla değerlendirilir. Test ortamı ve canlı işlem kabiliyeti ayrı kaydedilir.
- Öğrenci doğrulaması üniversite e-postasıyla kalır. Telefon, kimlik, kurum/yetkili doğrulaması sağlayıcıları ve üniversite öğrenci alan adı listesinin hazırlanması ayrıca ele alınır.
- Hesap/rol, profil, ilan/başvuru/davet, sözleşme/aşama, takım/çalışan, kredi işlemi, ödeme/fon/çekim, takip kaydı, gizlilik talebi ve uyuşmazlık için veri ve API sözleşmeleri çıkarılır.
- Saatlik dönem sınırları/saat dilimi, takımın farklı ücretleriyle haftalık ön fon hesabı, manuel/otomatik kayıt çakışması ve yeniden gönderim tekilliği tasarlanır.
- Görüntünün öğrenci tarafından işverene yayınlanmadan incelenebilmesi, talep sırasında bütün erişim kanallarının kapanması ve moderasyonun kabul/ret sonucunun görüntü/süre/ücrete etkisi tasarlanır. Doğrudan öğrenci silme veya otomatik ücret düşümü eklenmez.
- Kredi tutarları/fiyatları, öne çıkarma süre seçenekleri, hareketsizlik değeri, çekim alt limiti/takvimi ve saklama parametreleri için yapılandırma noktaları belirlenir. Kullanıcının sonraya bıraktığı rakamlar uydurulmaz.

**Kabul:** Her çekirdek modül için kaynak, sahibi, okuyabilen rol, durum geçişi, hata ve tekrar deneme davranışı tanımlanmış; sağlayıcı/stack seçimleri kanıtlanmış; karşılanamayan sağlayıcı kabiliyeti görünür iş olarak kaydedilmiş olmalıdır. Mimari belge bir özelliğin çalıştığı kanıtı değildir.

## 3. P1 — Hesap, profil ve görünürlük

E-posta/şifre kayıt/giriş/sıfırlama, aynı hesapta öğrenci/işveren rolleri, zorunlu/isteğe bağlı profil alanları ve genel/özel görünürlük uygulanır. Üniversite/bölüm, tanıtım, beceri ve saatlik ücret profilde yer alır; portföy/fotoğraf/link zorunlu değildir. Canlı doğrulama durumları veri modelinde bulunur ancak ilk testte ek doğrulama kapısı oluşturulmaz.

**Kabul:** M01/M02/M11 erişim kriterleri karşılanır; ziyaretçi başvuru, iletişim bilgisi ve özel dosya göremez; test hesabı doğrulaması yapılmış gibi sunulmaz. Responsive temel akışlar sonraki modüllerin kullanabileceği yapıdadır.

## 4. P2 — Yönetim, yapılandırma ve işlem kayıtları

Kategori/üniversite alan adı, kullanıcı/rol, test kredisi ve inceleme kuyruklarının yönetim temeli hazırlanır. Her operatör müdahalesi aktör, ilgili kayıt, neden ve sonuçla izlenir. Aylık dağıtım, yıllık doğrulama, 14/5 günlük inceleme, öne çıkarma bitişi ve 90 günlük temizlik için zamanlı işlem altyapısı kurulabilir; modül davranışları kendi paketlerinde bağlanır.

**Kabul:** M12 yönetim ve yetkili erişim sınırları korunur. Tekrar denenen kredi/ödeme/zamanlı işlem aynı etkiyi iki kez üretmez. Test ve canlı kayıtlar ayrıdır. Görüntü moderasyon kuyruğu P7'ye; uyuşmazlık ve çekim/iade kuyrukları P6/P8'e bağlanabilir.

## 5. P3 — Kredi, ilan, teklif ve öne çıkarma

Öğrenci/işveren bakiyeleri, başlangıç ve aylık kredi, satın alma/test satın alma, işlem/iade geçmişi; ilan alanları/yayın/başvuru son tarihi; teklif düzenleme/geri çekme, davet ve çoklu işe alım geliştirilir. Takım bakiyesi P5'te aynı kredi sözleşmesini tüketir. İlan ve başvuru öne çıkarma belirli süre/sabit kredi modelindedir.

**Kabul:** M03/M06 karşılanır. Bütün krediler süresiz; aylık dağıtım bakiyeyi sıfırlamaz; hesaplar arası transfer yoktur. Davet teklifi kredi harcamaz. İlan iptali/moderasyon iadesi, ret/geri çekme/süre dolmasının iadesizliği ve kullanılmamış öne çıkarma süresi iadesi ayrı kayıtlarla açıklanır. Tekrar gönderim ikinci teklif/kesinti/iade oluşturmaz.

## 6. P4 — Sözleşme, iletişim ve değerlendirme

Tekliften karşılıklı sözleşme kabulü, değişiklik, aşama/revizyon koşulları; başvuru/davet sonrası yazılı mesaj/dosya; sözleşmeye bağlı karşılıklı değerlendirme ve uygulama/e-posta bildirim tercihleri geliştirilir. Her işe alım ayrı sözleşmedir. Ses/video bu pakete eklenmez.

**Kabul:** M04/M11/M12'nin ilgili kriterleri karşılanır. Tek taraflı koşul değişikliği aktif ücret/kapsam olmaz. Başka sözleşmenin tarafı özel mesaj/dosya veya değerlendirmeye erişemez. Bildirimler görüntü moderasyonu engelini aşamaz.

## 7. P5 — Takımın çalışma modeli

Takım oluşturma/üyelik akışları, ayrı kredi bakiyesi, liderin başvuru/kabulü, sözleşmede çalışan üyeler ve ayrı saatlik ücretleri; üyenin mesaj/dosya/teslim/kendi süre yetkileri uygulanır. Aktif lider değişikliğinde işveren ve yönetim onayları kaydedilir; mevcut işin ödeme alıcısının kimliği ayrıca açıkça onaylanır. Üyelere ayrı ödeme veya iç kazanç dağıtımı yapılmaz.

**Kabul:** M05 karşılanır. Lider olmayan üye takım adına teklif/sözleşme kabul edemez; çalışan üyenin iş yetkileri kullanılabilir. Lider değişikliği geçmiş kazancın alıcısını örtük olarak değiştirmez. Canlı tüm üye uygunluğu P9'da etkinleştirilir; ilk testte ek doğrulama ertelenir.

## 8. P6 — Para ve sabit ücretli iş

Test ortamında fonlama, %10 freelancer komisyonu, aşama teslimi/onayı, 14 günlük yanıtsızlıkta serbest bırakma, revizyon/yeniden teslim, uyuşmazlık bekletme, iptal/iade ve banka çekim talebi geliştirilir. İşveren iş bedeline ek platform komisyonu ödemez. Ödeme durumları ile gerçek aktarım sonucu ayrıdır.

**Kabul:** M07/M09 karşılanır. Fonlanmamış aşamada yeni ücretli çalışma başlamaz. Yeniden teslim 14 günlük süreyi yeniden başlatır; açık revizyon/itirazda eski sayaç ödeme yaptıramaz. İptal onaylanan/başlanmamış/yapılmış-onaysız kısımları ayrı sonuçlandırır. Tekrar denenen serbest bırakma/iade/çekim ikinci para hareketi üretmez. Test işlemleri gerçek kazanç oluşturmaz.

## 9. P7 — Üç OS tracker, günlük ve görüntü moderasyonu

Windows/macOS/Linux paketleri, sözleşme/ekran seçimi, süre/açıklama, etkinlik sayısı/aktif uygulama, her 10 dakikalık bölümde seçili ekrandan rastgele görüntü; hareketsizlikte duraklama/devam, offline kayıt ve tekil senkronizasyon geliştirilir. Web günlüğü ile yönetim incelemesi aynı erişim sözleşmesini kullanır.

Kişisel bilgi talebi işveren görmeden açılabilir. Öğrenci doğrudan görüntü silemez. Talep edilen görüntü sonuçlanana kadar günlük, küçük resim, doğrudan bağlantı, indirme, rapor ve bildirim dahil bütün işveren yollarında kapalıdır. Talep otomatik süre/ücret düşürmez; P0'da sonuçlandırılan moderasyon tasarımı uygulanır. Ekran/ayrıntılı etkinlik 90 gün; açık itirazın ilgili kayıtları sonuca kadar korunur.

**Kabul:** M10 karşılanır. Üç OS ilk canlı kapsamda hazırdır; yalnız tarayıcı sayacı eşdeğer teslim değildir. Tuş içeriği/kamera/video alınmaz. Offline tekrar gönderim çift ücret üretmez. Görüntünün ana günlükten gizlenip başka kanaldan görünmesi kabul edilmez. Temizlik açık itiraz kanıtını silmez; ödeme/sözleşmeye otomatik 90 gün uygulanmaz.

## 10. P8 — Saatlik hesaplama ve ödeme

Haftalık saat sınırı ve artış onayı, haftalık ön fonlama, kullanılmamış fonun iade/aktarma seçimi, üye bazlı ücretlerle toplam takım limiti, açık işveren onaylı manuel süre, haftalık hesap ve 5 günlük inceleme/itiraz dönemi P6/P7 kayıtlarıyla bütünleştirilir.

**Kabul:** M08 ve ilgili M05/M07 kriterleri karşılanır. Sınır artışı onaysız gerçekleşmez; manuel süre onaysız ücretlenmez. Bir süre otomatik/manuel/offline tekrarlarıyla ikinci kez hesaplanmaz. İtiraz ilgili ödeme serbest bırakmasını durdurur. Takım hesabı yalnız liderin kendi süresine indirgenmez.

## 11. P9 — İlk çekirdeğin tamamlanması ve canlı hazırlık

- Bütün ilk sürüm ekranları mobil uyumlu webde bütünleştirilir. FIRST kullanımı zorunlu olmadan proje/katkı linkleri portföye eklenir; otomatik aktarım/ortak giriş eklenmez.
- Yönetim ilan şikâyeti, kredi/iade, başarısız fonlama/çekim, uyuşmazlık, görüntü incelemesi ve lider değişikliği için gerekli işlemleri tamamlayabilir.
- Ürün hazırlandıktan sonra yalnız üniversite e-postasıyla doğrulama, yıllık yenileme/mezuniyet davranışı, birey/kurum işveren kontrolü ve takım çalışanlarının uygunluğu etkinleştirilir.
- Sağlayıcı canlı yapılandırması, üniversite alan adı listesi, seçilmiş sayısal ayarlar, masaüstü dağıtım/güncelleme ve operasyon sorumlulukları tamamlanır. Test kredisi/ödeme/kazanç kayıtları canlıya taşınmaz.

**Kabul:** Tam kapsamdaki bütün M01–M12 kriterleri ve değişmezler birlikte karşılanır. Test aşamasının doğrulama ertelemesi canlı ürün davranışı olarak kalmaz. Üç OS ve yönetim/gizlilik/ödeme akışlarından biri eksikken ilk canlı kapsam tamamlandı denmez. Kaynak incelemesi ve varsa ayrıca yetkilendirilmiş çalışma zamanı/sağlayıcı doğrulaması ayrı raporlanır.

## 12. Bütün paketlerde ortak tamamlanma şartları

- Gerçek dosya sahipliği ve ortak API/veri/rol sözleşmesi görev başlamadan yazılır. Aynı dosyaya paralel writer verilmez; bağımlılığı tamamlanmış farklı kapsamlar ayrı yürütülebilir.
- Ağ kesintisi, tekrar gönderim ve zamanlı işin yeniden çalışması ikinci kredi kesintisi/iade/fonlama/ödeme üretmez. Yeniden teslim/itiraz sayaç ve ödeme durumuyla tutarlıdır.
- Özel veri ve dosya erişimi yalnız UI'da gizlemeyle karşılanmaz; ilgili bütün erişim yolları aynı yetki/moderasyon durumunu uygular.
- Hatalı fonlama, çekim, iade, uyuşmazlık ve görüntü talebi operatör tarafından izlenebilir; operatör müdahalesi geçmiş işlem kaydını gizlemez.
- Her görevde ilgili AK kriterleri kaynak/diff ile değerlendirilir. Kullanıcı ayrıca istemedikçe test/lint/typecheck/browser/computer use çalıştırılmaz; çalıştırılmamış davranış doğrulanmış gösterilmez.
- Dosya değişen accepted teslimlerde ana integration sahibi anlamlı commit/push yapar ve remote hash doğrular; alt writer bağımsız push yapmaz. FIRST'ün diğer AI kaynakları ve run'ları korunur.

## 13. İlk sürüm sonrası paketler

| Paket | Kapsam ve sınır |
|---|---|
| Ortak kimlik ve FIRST aktarımı | Ortak giriş ve otomatik proje/katkı referansları; kaynak yetkileri korunur. Tek backend/DB/SSO ürünü varsayılmaz. |
| AI ilan desteği | Başlık/açıklama/kapsam/aşama taslağı; süre/bütçe işveren onaylı. Tahmin garantisi veya otomatik yayın kararı eklenmez. |
| INTO inceleme bağlantısı | İsteğe bağlı kapsam/teslim incelemesi; tarafların bilgi paylaşım onayı ve mentor kabulü. STEP uyuşmazlık desteğinden ayrı mentorluk ilişkisidir. |
| Diğer ürün genişlemeleri | Yerel mobil uygulama, hazır hizmet paketleri, abonelik, sesli/görüntülü görüşme, öne çıkarma açık artırması ve diğer para birimleri için ayrı teknik/ürün paketleri. |

P0–P9 için kaynak uygulaması ve bağımsız inceleme teslimi yapıldı. İlk canlı kabul için gerçek sağlayıcı/banka kabiliyetleri, doğrulama hesapları/alan adı listesi, onaylı politika ve OS paket dağıtımı tamamlanmalıdır. Kaynak teslimi bu dış kapıların veya çalışma zamanı doğrulamasının tamamlandığını göstermez.
