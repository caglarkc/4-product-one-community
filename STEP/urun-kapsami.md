# STEP — Tam ürün kapsamı

Tarih: 30 Eylül 2026 (Europe/Istanbul). Bu belge, [52 sorunun kabul edilen yanıtlarını](soru-karar-eslestirmesi.md) ürün modülleri, ekranlar, akışlar ve kabul kriterlerine dönüştürür. Karar matrisi kaynak kayıttır; 24/45/47/49 numaralı kullanıcı istisnaları diğer önerilere göre önceliklidir. Önceki %10 komisyon, ön fonlama, takım lideri ve takip kararları birlikte uygulanır.

Bu bir ürün spesifikasyonudur. Aşağıdaki davranışlar uygulanmış veya test edilmiş olarak sunulmaz. Kabul kriterleri geliştirme teslimlerinin nasıl değerlendirileceğini tanımlar. Sayısal olarak sonraya bırakılmış parametreler, sağlayıcılar ve teknik mimari seçilmiş değildir. Geliştirme sırası [geliştirme planında](gelistirme-plani.md), karar özeti [kararlarda](kararlar.md) tutulur.

## 1. Ürünün amacı ve sınırları

STEP, üniversite öğrencilerinin bireysel veya takım olarak ücretli hizmet sunduğu, birey ve kurumların bu hizmetleri satın aldığı pazardır. İlk hizmet alanları yazılım, veri/AI, tasarım, video, çeviri ve içerik üretimidir; kategori listesi genişletilebilir. Video hizmet kategorisidir; ilk sürümün iletişim aracı olarak görüntülü görüşme içerdiği anlamına gelmez.

Ücretli çalışma ilişkisinin kapsamı STEP'tedir. FIRST'te birlikte üretmek, ekip bulmak ve açık kaynak katkısı yapmak ayrı topluluk ilişkisidir; public/private repo ayrımı ücretli iş sınırını değiştirmez. FIRST üyeliği veya geçmişi STEP'e katılmak için şart değildir. Kullanıcı proje ve katkı bağlantılarını STEP portföyüne ilk sürümde ekleyebilir; FIRST'ten otomatik aktarım sonraki entegrasyondur. Bağlantı eklemek kapalı proje, kod veya özel dosyalara erişim sağlamaz.

INTO ile kapsam/teslim incelemesi sonraki sürümde isteğe bağlıdır; iş bilgisinin paylaşımını taraflar onaylar ve mentorun kabulü gerekir. PATH aynı probleme farklı çözümlerin yarışmasına odaklanır; STEP'in bir iş için taraflarla sözleşme yapması yarışma değildir. Dört ürünün ayrı site yönü korunur. Ortak hesap/giriş ayrı entegrasyon aşamasıdır; ortak veritabanı, tek backend veya SSO aracı kararı bulunmaz.

## 2. Aktörler ve erişim sınırları

| Aktör | Ürün içindeki sorumluluk ve erişim |
|---|---|
| Ziyaretçi | İlan ve profil genel bilgilerini giriş yapmadan inceleyebilir. İletişim bilgileri, başvurular ve özel dosyalar bu genel görünürlüğe dahil değildir. |
| Öğrenci freelancer | Profilini ve portföyünü yönetir, ilana teklif verir, davete yanıt verir, bireysel sözleşmesini kabul eder; kendi teslimlerini ve sürelerini kaydeder, kazanç çekimi ister. |
| Bireysel işveren | İlan açar, öğrenci/takım davet eder, teklifleri değerlendirir, sözleşme/fonlama işlemlerini ve çalışma/teslim incelemesini yürütür. |
| Kurumsal işveren | İşveren akışlarına kurum ve yetkili doğrulamasıyla katılır. Kurum içi ayrıntılı kullanıcı/yetki yapısı teknik tasarımda belirlenir. |
| Takım lideri | Takım adına başvurur ve sözleşmeyi kabul eder; ayrı takım kredi bakiyesini yönetir, takım kazancı için kendi adına banka hesabına çekim talebi oluşturur. |
| İşe dahil takım üyesi | İlgili işte mesajlaşır, dosya ve teslim yükler, kendi çalışma süresini kaydeder. Takım adına başvuru/sözleşme kabulü ve kazanç alımı liderdedir. |
| STEP destek/moderasyon görevlisi | Yetkili inceleme kapsamında şikâyet, uyuşmazlık ve kişisel bilgi taleplerini değerlendirir. Takip verisine genel ve sınırsız erişim rolü değildir. |
| Yönetim | Üniversite e-posta alan adlarını, kategori listesini ve test kredilerini yönetir; ürünün moderasyon, ödeme/itiraz ve takım lideri değişikliği işlemlerini yönetim panelinden yürütür. Ayrıntılı görev/yetki dağılımı teknik tasarım işidir. |

Aynı öğrenci hesabı işveren rolünü de kullanabilir; işveren işlemleri için işveren doğrulamalarını tamamlar. Rol kullanabilmek her veriye erişim hakkı vermez. Bir ilandan birden fazla öğrenci veya takım alınabilir; her işe alım kendi sözleşmesine sahiptir. Bir sözleşmenin teklifleri, özel dosyaları, teslimleri ve takip kayıtları diğer işe alımlar için açılmaz.

Öğrenci kendi takip kayıtlarını, işveren yalnız ilgili sözleşmenin kayıtlarını görür. Takım liderliği başka üyelerin görüntülerine otomatik erişim izni olarak kullanılmaz. Destek erişimi yetkili incelemeyle sınırlıdır. Genel ilan/profil görünürlüğü iletişim, mesajlaşma, başvuru ve özel dosya görünürlüğünün yerine geçmez.

## 3. Test, ilk canlı sürüm ve sonraki sürümler

| Aşama | Kapsam |
|---|---|
| Ürün testi | E-posta/şifre girişi ve şifre sıfırlama; öğrenci ve işveren ek doğrulama kapıları ertelenir. Ödeme sağlayıcısının test ortamında deneme ödemeleri, yönetimden verilen test kredileri kullanılır. Testte gerçek para hareketi ürün doğrulaması gibi sunulmaz. |
| Canlıya hazırlık | Ürün hazırlandıktan sonra öğrenci uygunluğu/üniversite e-postası ve işveren doğrulamaları etkinleştirilir. Sağlayıcı, tutar, kredi maliyeti, operasyon ve teknik parametrelerin ilgili açık işleri sonuçlandırılır. |
| İlk canlı sürüm | Mobil uyumlu web; hesap/profil, keşif/ilan/başvuru/davet, takım, kredi/öne çıkarma, sözleşme, saatlik/sabit ödeme, yazılı mesaj/dosya, değerlendirme, bildirim, yönetim paneli ve Windows/macOS/Linux takip istemcisi. Portföye proje/katkı bağlantıları dahildir. |
| Sonraki sürümler | AI ilan desteği, INTO inceleme bağlantısı, FIRST otomatik veri aktarımı ve ortak giriş entegrasyonu; yerel mobil uygulama, hazır hizmet paketi kataloğu, abonelik, sesli/görüntülü görüşme ve öne çıkarmada açık artırma. Diğer para birimleri sonraki genişlemededir. |

Sonraki sürümün AI ilan desteği; başlık, açıklama, kapsam ve aşama taslağı hazırlamaya yardımcı olur. Süre/bütçe önerilerini işveren onaylar; sağlayıcı ve tahmin yöntemi seçilmemiştir. Bu yön, ilk canlı sürümde AI desteği bulunması taahhüdü değildir.

Canlı öğrenci uygunluğu; Türkiye'deki bütün üniversitelerin önlisans, lisans, yüksek lisans ve doktora öğrencilerini, 18 yaş ve üzeri koşuluyla kapsar. Kabul edilen üniversite e-posta alan adları yönetimden tanımlanır. Üniversite adresi olmayan kişi doğrulanana kadar yeni başvuru yapamaz. Üniversite e-posta doğrulaması yıllık yenilenir. Mezuniyet veya adrese erişim kaybında mevcut işlerin tamamlanması mümkündür; yeni başvurular kapanır. Üniversite e-postasına erişim, bağımsız ve sürekli öğrenci kayıt sorgusu yapılmış gibi sunulmaz.

Canlı işveren ilan yayımlamadan önce bireyde telefon ve kimlik; kurumda ayrıca kurum bilgisi ve yetkili doğrulamasını tamamlar. Doğrulama sağlayıcısı ve yöntemi seçilmemiştir. İlk testte bu canlı kapıları zorunlu tutulmaz. Takımın işe katılan bütün üyelerinin canlı öğrenci doğrulaması tamamlanmış olur; bu kural ilk testte doğrulamaları erkene çekmez.

## 4. Ekran ve çalışma alanları

Aşağıdaki adlar ekranların ürün sorumluluğunu anlatır; onaylanmış URL veya görsel tasarım değildir. Web alanları mobil uyumlu sunulur. Takip kaydı Windows/macOS/Linux istemcileriyle yürütülür.

| Alan | Temel aktör ve içerik |
|---|---|
| Kayıt, giriş, şifre sıfırlama | E-posta/şifre hesabı; canlı aşamada rolüne göre doğrulama durumu ve yenileme ihtiyacı. |
| Öğrenci profil düzenleme / genel profil | Üniversite/bölüm, tanıtım, beceriler, saatlik ücret; isteğe bağlı fotoğraf, portföy, dış/proje/katkı bağlantıları. Genel ve özel bilgi ayrımı. |
| İlan keşfi / ilan detayı | Genel ilan bilgileri; çalışma türü, bütçe ve beklenen süre. Başvuru veya davete yanıt giriş gerektiren işlemlerdir. |
| İşveren ilan yönetimi | Oluşturma, yayın, başvuru son tarihi, başvurular/davetler, birden fazla işe alım ve iptal. |
| Teklif oluşturma / başvurular | Teklif metni, ücret, süre, isteğe bağlı iş örneği; seçim öncesi düzenleme/geri çekme; kredi etkisi. |
| Takım alanı | Lider, işe dahil üyeler, ayrı kredi bakiyesi, takım adına başvuru ve sözleşme sorumluluğu. Ayrıntılı takım oluşturma/üyelik ekranı teknik akış tasarımında tamamlanır. |
| Kredi ve öne çıkarma | Kişisel veya takım bakiyesi, ücretsiz/satın alınmış krediler, işlem ve iade kayıtları; ilan/başvuru için süreli görünürlük. |
| Sözleşme çalışma alanı | Kabul edilen kapsam, ücret, süre/aşamalar, taraflar ve takım çalışanları; değişikliklerin karşılıklı kabulü. |
| Mesajlar ve dosyalar | Başvuru/davet sonrası görüşme; sözleşme öncesi platform içi yazılı iletişim ve dosya paylaşımı. |
| Saatlik çalışma günlüğü | Üye bazlı süre/açıklama, haftalık sınır ve fonlama, manuel süre onayı, 5 günlük işveren incelemesi/itiraz. |
| Sabit iş teslimleri | Aşama fonlama, teslim, onay/revizyon, yeniden teslim ve 14 günlük inceleme. |
| Ödeme, kazanç ve çekim | Fonlanmış iş bedeli, bekleyen/serbest bırakılan/tartışmalı ödeme, %10 komisyon, iade veya sonraki haftaya aktarım ve banka çekim talebi. |
| Bildirim ve değerlendirme | Uygulama içi/e-posta tercihleri; sözleşmeye bağlı karşılıklı puan/yorum. |
| Destek ve kişisel bilgi talebi | İtiraz, şikâyet, kredi iadesi talebi ve işveren görünürlüğünden önce açılabilen ekran görüntüsü moderasyon talebi. |
| Yönetim paneli | Üniversite alan adları/kategoriler, test kredileri, ilan şikâyetleri, uyuşmazlıklar, görüntü incelemesi ve lider/ödeme alıcısı değişikliği onayları. |
| Takip istemcisi | Sözleşme ve seçilen ekran; başlat/duraklat/devam; süre, açıklama, kayıt ve bağlantı/senkronizasyon durumu; kişisel bilgi talebine erişim. |

## 5. Modüller, akışlar ve kabul kriterleri

### M01 — Hesap, uygunluk ve rol doğrulamaları

Kaynak kararlar: 1–6, 35, 48, 51–52.

Kayıt → e-posta/şifreyle giriş → profil/rol işlemleri akışı kullanılır. Şifre sıfırlama hesap modülündedir. Canlı aşamada öğrenci uygunluğu ve işveren yayımlama doğrulamaları ayrı kapılardır. STEP testleri FIRST'ten bağımsız başlar. Aynı hesapta öğrenci ve işveren işlemleri rolün kendi kurallarını uygular.

Kabul kriterleri:

- **AK-01.1:** İlk testte öğrenci/işveren ek doğrulamaları eksik olduğu için test ilanı veya başvurusu engellenmez; canlı davranışıyla test istisnası belgelenir.
- **AK-01.2:** Canlıda 18 yaş ve eğitim düzeyi uygunluğu, yönetimin kabul ettiği üniversite e-posta alan adı/doğrulaması ve yıllık yenileme kuralları başvuru uygunluğunda uygulanır.
- **AK-01.3:** Mezuniyet veya e-posta erişimi kaybı yeni başvuru kapısını kapatır; mevcut sözleşmenin tamamlanmasını otomatik engellemez.
- **AK-01.4:** Canlı bireysel işveren telefon/kimlik; kurumsal işveren ayrıca kurum/yetkili doğrulaması tamamlanmadan ilan yayımlayamaz. Öğrenci doğrulaması bu kapının yerine geçmez.
- **AK-01.5:** STEP hesabı FIRST hesabı veya ortak giriş entegrasyonu bulunmadığı için kullanılamaz hâle gelmez; ortak teknik kimlik seçilmiş gibi uygulanmaz.

### M02 — Profil, portföy, kategori ve genel keşif

Kaynak kararlar: 7–9, 47.

Öğrenci profilini oluşturur/düzenler; genel profil üzerinden beceri, saatlik ücret ve isteğe bağlı portföyünü sunar. FIRST veya başka üretim alanlarından proje/katkı bağlantısı eklenebilir. Kategoriler ilanları ve hizmet alanlarını ifade eder; hazır hizmet paketi satış kataloğu değildir.

Kabul kriterleri:

- **AK-02.1:** Üniversite/bölüm, kısa tanıtım, beceriler ve saatlik ücret eksik profil zorunlu alanları tamamlanmış sayılmaz; fotoğraf, portföy ve dış bağlantı zorunlu yapılmaz.
- **AK-02.2:** İlk kategori listesi altı kabul edilen hizmet alanını içerir ve genişletilebilir; yalnız yazılım hizmetine daraltılmaz.
- **AK-02.3:** Girişsiz ziyaretçi genel ilan/profil bilgilerini görebilir; bu erişim iletişim bilgisi, başvurular, özel dosyalar veya mesajlaşmayı açmaz.
- **AK-02.4:** Proje/katkı linkleri ilk canlı sürüm portföyünde kullanılabilir. FIRST zorunluluğu, otomatik veri çekimi veya özel proje erişimi bağlantı ekleme davranışına dahil edilmez.

### M03 — İlan, teklif, davet ve işe alım

Kaynak kararlar: 10–14, 16, 25–27.

İşveren ilanı hazırlar → ilan açma kredisiyle ve ilgili aşamanın doğrulama koşuluyla yayımlar → teklif/davet görüşmeleri yürür → öğrenci veya takım seçilir → ayrı sözleşme kurulur. İlan başlık, açıklama, kategori, beceriler, çalışma türü, bütçe ve beklenen süre içerir; dosya eki isteğe bağlıdır. İşveren son başvuru tarihi seçebilir. Doğrulanmış işverenin ilanı yayın öncesi moderasyon sırası beklemez; şikâyet sonrası incelenebilir.

Öğrenci teklif metni, ücret ve süre verir; iş örneği isteğe bağlıdır. Seçimden önce teklifi düzenleyebilir veya geri çekebilir. İşveren öğrenci veya takımı ilana davet edebilir; davet yanıtında başvuru kredisi harcanmaz. Bir ilandan birden fazla işe alım yapılırsa tek ortak sözleşmeye zorlanmaz.

Kabul kriterleri:

- **AK-03.1:** Zorunlu ilan/teklif alanları doğrulanır; isteğe bağlı dosya veya iş örneği zorunlu alan hâline gelmez.
- **AK-03.2:** Canlıda doğrulanmış işverenin geçerli ilanı hemen yayımlanır; test aşamasının ertelenen doğrulamaları korunur.
- **AK-03.3:** Seçimden önce düzenleme/geri çekme yapılabilir. İlan davetine verilen teklifte başvuru kredisi kesilmez.
- **AK-03.4:** Bir ilandan birden fazla işe alım oluştuğunda kapsam/fonlama/teslim ve yetkileri ayrı sözleşmeler üzerinden yönetilir; sayı için ürünün kabul etmediği üst limit eklenmez.
- **AK-03.5:** Reddedilen, geri çekilen veya süresi dolan başvuru için kredi geri verilmez; ilan iptali/moderasyon iadesi M06'ya göre ayrı değerlendirilir.

### M04 — Sözleşme, değişiklik ve iş yaşam döngüsü

Kaynak kararlar: 15, 18–20; önceki aşama/ön fonlama kararları.

Seçim → kapsam/ücret/süre/aşamaların karşılıklı kabulü → fonlama → çalışma → teslim/inceleme → ödeme ve tamamlanma akışı bulunur. Sonradan kapsam ve koşul değişiklikleri de iki tarafın kabulünü gerektirir. Revizyon koşulları sözleşmede belirtilir; kapsam dışı talepler ek ücret veya aşama gerektirir.

Uyuşmazlıkta ilgili ödeme bekletilir. Taraflar anlaşamazsa STEP destek ekibi kayıtları inceleyip sonuçlandırır. İptalde onaylanan kısımlar ödenir, başlanmamış kısımların fonu işverene döner. Yapılmış fakat onaylanmamış çalışma uyuşmazlık üzerinden değerlendirilir; otomatik yok sayılmaz veya otomatik onaylanmaz.

Kabul kriterleri:

- **AK-04.1:** Karşılıklı kabul edilmemiş kapsam/ücret/süre/aşama değişikliği aktif sözleşme koşulu gibi kullanılmaz.
- **AK-04.2:** Kapsam dışı revizyon kabul edilen işin bedelsiz uzaması sayılmaz; yeni ücret/aşama karşılıklı kabul akışına gider.
- **AK-04.3:** İtirazın ilgili ödemesi inceleme sonuçlanmadan serbest bırakılmaz; destek incelemesi işin kayıtlarını ve tarafların taleplerini birbirine bağlar.
- **AK-04.4:** İptal; onaylanan, başlanmamış ve yapılmış/onaylanmamış kısımları ayrı sonuçlandırır. İş bedeli iptali ile kredi iadesi tek işlem gibi varsayılmaz.

### M05 — Takım, çalışan üyeler ve lider yetkisi

Kaynak kararlar: 13–15, 33, 35–40; önceki lider kararı.

Takım iş alabilir; işe katılan üyeler sözleşmede listelenir. Takım adına başvuru ve sözleşme kabulü liderdedir. Üyeler ilgili sözleşmenin mesajlaşma, dosya/teslim ve kendi süre kayıtlarında çalışır. Takımın kredi hesabı kişisel bakiyeden ayrıdır ve lider tarafından yönetilir.

Saatlik takım işinde çalışan üyelerin ücretleri sözleşmede ayrı belirlenir; bütün üyelerin süreleri takımın haftalık sınırına sayılır. İlk sürümde platform kazancı lidere öder/gösterir; iç dağıtım takıma aittir, üyelere ayrı ödeme yapılmaz. Aktif işte lider değişikliği işveren ve yönetim onayı gerektirir; mevcut işin ödeme alıcısı ayrıca açıkça onaylanır.

Kabul kriterleri:

- **AK-05.1:** Lider olmayan üye takım adına teklif gönderemez veya sözleşme kabul edemez; işe dahil üyenin kendi mesaj/dosya/teslim/süre işlemleri kullanılabilir.
- **AK-05.2:** Canlıda işe katılan üyelerin tamamı doğrulanmış öğrencidir; ilk testte ek doğrulama kapısının ertelenmesi korunur.
- **AK-05.3:** Üyelerin farklı saatlik ücretleri ve kendi süreleri ayrı gösterilir; süreler ortak takım haftalık sınırını tüketir.
- **AK-05.4:** Takım kredisi kişisel krediyle karışmaz; liderin yetkisi hesaptan hesaba kredi aktarımı izni olarak yorumlanmaz.
- **AK-05.5:** Aktif işte lider değişikliği işveren/yönetim onayı olmadan kesinleşmez. Lider değişti diye mevcut ödeme alıcısı örtük olarak değiştirilmez.
- **AK-05.6:** Takım ödeme kaydı liderde sonuçlanır; platform üyeler arasında dağıtım yapılmış gibi kayıt üretmez. Lider kendi adına banka hesabına çekim ister.

### M06 — Kredi, ücretsiz haklar, öne çıkarma ve iadeler

Kaynak kararlar: 23–27, 36, 51; önceki kredi kararları.

İş bedeli gerçek para; kredi ilan açma, başvuru ve öne çıkarma gibi platform işlemleri içindir. Başvuru/ilan açma başlangıçta sabit kredi maliyeti kullanır. Öğrenci ve işverene başlangıç ve aylık ücretsiz kredi verilir; tutarlar belirlenmemiştir. Satın alınmış ve ücretsiz bütün krediler süresizdir, aylık krediler silinmez, hesaplar arasında kredi aktarılmaz.

İlk sürümde ilan ve başvuru belirli süre için sabit krediyle öne çıkarılabilir; açık artırma yoktur. İlan iptali veya moderasyonla kaldırmada ilan açma ve ilgili başvuru kredileri ilgili bakiyelere döner. Kaldırılan ilanın kullanılmamış öne çıkarma süresi kredi olarak iade edilir. Kullanılmamış satın alınmış kredi için iade talebi alınır; kesin koşullar sağlayıcı seçimiyle tamamlanır. İş anlaşması sonrasındaki iptalin kredi ayrıntıları ayrıca tasarlanır.

Kabul kriterleri:

- **AK-06.1:** Kredi harcaması öğrenci iş ücretini fonlamış veya ödemiş sayılmaz; kredi ve TL iş bedeli ayrı kaydedilir/sunulur.
- **AK-06.2:** Ücretsiz ve satın alınmış krediler süre dolduğu için silinmez; aylık dağıtım önceki kalan krediyi sıfırlamaz. Hesaplar arası transfer işlemi sunulmaz.
- **AK-06.3:** Sabit kredi maliyetleri ve ücretsiz dağıtım tutarları belirlenmeden sayısal değer uydurulmaz. Test kredileri yönetimden verilir; canlı ücretsiz haklarla karıştırılmaz.
- **AK-06.4:** Davet yanıtı için başvuru kredisi düşmez; ret/geri çekme/süre dolması kredi iadesi oluşturmaz.
- **AK-06.5:** İlan iptali veya moderasyonla kaldırmada ilan açma ve ilgili başvuru kredileri ilgili kişisel/takım bakiyelerine iade edilir. Kullanılmamış öne çıkarma süresinin kredi iadesi ayrı kayıtla açıklanır.
- **AK-06.6:** İlk öne çıkarma sabit kredi ve süre kullanır; açık artırma veya abonelik şartı getirilmez. Satın alınmış kullanılmamış kredi iadesi talebi, koşulsuz otomatik para iadesi gibi gösterilmez.

### M07 — İş bedeli, fonlama, komisyon ve çekim

Kaynak kararlar: 19–20, 28, 32–34, 39–40, 51; önceki %10/ön fonlama kararları.

İlk canlı sürüm iş bedelleri TL'dir. Freelancer iş bedelinden %10 komisyon kesilir; işveren iş bedeline ek platform komisyonu ödemez. Ödeme sağlayıcısı, aktarım takvimi, çekim alt limiti ve uygulama ayrıntıları seçilmiş değildir. Freelancer veya takım lideri kendi adına banka hesabına çekim talebi oluşturur.

Saatlikte haftalık sınıra karşılık gelen bedel çalışma başlamadan; sabit işte her aşama önceden fonlanır. Fonlama başarısızsa yeni ücretli çalışma başlamaz; taraflar bildirilir, fonlama tamamlanınca devam edilir. Uyuşmazlık ilgili ödemeyi bekletir. Kullanılmayan haftalık fonun iadesi veya sonraki haftaya aktarımı seçilebilir. Çekim talebi oluşturmak bankaya ödeme yapılmış demek değildir.

Kabul kriterleri:

- **AK-07.1:** Canlı TL iş bedeli ve %10 freelancer komisyonu açıklanır; işverene ek platform komisyonu eklenmez. Teknik sağlayıcı maliyetleri için yeni ürün fiyatı varsayılmaz.
- **AK-07.2:** Fonlama tamamlanmadan yeni ücretli çalışma başlatılmaz; başarısızlık ve devam durumu tarafların bildirimlerine yansır.
- **AK-07.3:** Ön fonlama, inceleme, itiraz bekletmesi, serbest bırakma ve çekim talebi birbirinden ayırt edilir; talep veya fonlama gerçekleşmiş kazanç aktarımı gibi gösterilmez.
- **AK-07.4:** Kullanılmayan saatlik fonun iade veya sonraki haftaya aktarım seçimi uygulanır; uyuşmazlık konusu tutar çözülmeden bu yoldan serbest bırakılmaz.
- **AK-07.5:** Bireysel kazanç öğrenciye, takım kazancı lidere yönelir; alıcı kendi adına banka hesabına çekim talep eder. Alt limit/takvim sağlayıcı keşfi sonuçlanmadan uydurulmaz.
- **AK-07.6:** İlk ürün testinde test ortamı/deneme ödeme işlemleri kullanılır; gerçek para hareketi yapılmış veya sağlayıcı canlı entegrasyonu doğrulanmış gibi raporlanmaz.

### M08 — Saatlik iş ve haftalık inceleme

Kaynak kararlar: 29–32, 34, 38, 41–46; önceki zorunlu takip kararı.

Karşılıklı sözleşme koşulları ve haftalık sınır → ön fonlama → zorunlu takip → haftalık hesaplama → işverenin 5 günlük inceleme/itiraz süresi → ilgili ödeme akışı yürür. Haftalık sınır artışı işveren onayı gerektirir; sözleşme değişikliklerinde M04'ün karşılıklı kabul kuralı korunur. Manuel süre eklenebilir; yalnız işverenin açık onayıyla ücretlendirilir. Takım işinde üyelerin süre toplamı takım sınırına sayılır.

Kabul kriterleri:

- **AK-08.1:** Saatlik çalışma takip gerektirir; manuel süre kaydı bu şartı kaldıran sınırsız ve onaysız ücret kaynağı değildir.
- **AK-08.2:** Saatlik hesap haftalık döneme ve kabul edilmiş sınıra dayanır; işveren onayı olmayan sınır artışı ücret hesabına yansıtılmaz. Dönem saat dilimi/başlangıç saati henüz seçilmemiştir.
- **AK-08.3:** Manuel süre onay verilmeden ücretlendirilmez; aynı sürenin otomatik kayıt veya tekrar gönderimle yeniden ücretlendirilmesi engellenir.
- **AK-08.4:** İşveren 5 günlük inceleme/itiraz olanağını kullanabilir; ilgili ödeme itiraz sonucu beklenirken yapılmaz. İnceleme ardından ödeme M07'ye bağlı yürür.
- **AK-08.5:** Takım toplamı üyelerin ayrı süre/ücret kayıtlarıyla açıklanabilir; yalnız liderin kendi süresine indirilmez.

### M09 — Sabit ücretli iş, aşamalar ve teslim onayı

Kaynak kararlar: 15, 18–20; önceki tek/çok aşama, ön fonlama, 14 gün kararları.

Tek veya çok aşamalı sözleşme → ilgili aşamanın ön fonlaması → çalışma → teslim → işveren onayı, revizyon veya itiraz → ödeme akışı yürür. Onayla veya teslimden sonra 14 günlük yanıtsızlıkla ödeme serbest bırakılır. Revizyon koşulları sözleşmede belirlenir. Yeniden teslimde 14 günlük inceleme süresi yeniden başlar. İtiraz ilgili ödemeyi bekletir. Sabit işte tracker kullanımı tarafların tercihidir; takip süresi sabit iş bedelini kendiliğinden saatlik bedele çevirmemelidir.

Kabul kriterleri:

- **AK-09.1:** Tek aşamalı ve çok aşamalı işler desteklenir; ilgili aşama önceden fonlanmadan yeni ücretli çalışma başlamaz.
- **AK-09.2:** Teslimin ardından onay veya 14 günlük yanıtsızlık ödeme serbest bırakma koşulu olur; açık revizyon/itiraz bu sessizlik koşuluyla atlanmaz.
- **AK-09.3:** Yeniden teslim, 14 günlük inceleme süresini yeniden başlatır; ilk teslimin eski sayacı yeniden teslimi incelemeden ödeme yaptırmaz.
- **AK-09.4:** Kapsam dışı talep yeni ücret/aşama ve karşılıklı kabul gerektirir; takip istemcisinin açılması sabit fiyat sözleşmesini saatlik fiyat sözleşmesine dönüştürmez.

### M10 — Masaüstü takip, çalışma günlüğü ve kişisel bilgi koruması

Kaynak kararlar: 41–46, 52; önceki zorunlu/isteğe bağlı takip kararı.

İlk canlı sürüm Windows, macOS ve Linux istemcilerini içerir. Kullanıcı ilgili sözleşme ve takip edilecek ekranı seçer. Kayıt; süre, çalışma açıklaması, ekran görüntüsü, fare/klavye etkinlik sayısı ve aktif uygulama bilgisinden oluşur. Tuş içeriği, kamera görüntüsü veya sürekli video kaydı alınmaz. Her 10 dakikalık bölümde rastgele bir görüntü yalnız seçilen ekrandan alınır. Hareketsizlik belirlenen süreden sonra otomatik duraklatır; devam seçeneği sunulur. Süre değeri teknik tasarımda belirlenir.

Çevrimdışıyken kayıt yerelde devam eder; bağlantı gelince gönderilir. Gönderim tekrarları aynı süreyi birden fazla kez ücretlendiremez. Öğrenci kendi kayıtlarını görür; işveren ilgili sözleşmenin kayıtlarını görür. Destek erişimi yalnız yetkili incelemedir.

Öğrenci ekran görüntüsünü doğrudan silemez. Kişisel bilgi içeren bir görüntü için **işverene gösterilmeden önce** moderasyon talebi oluşturabilir. Talep konusu görüntü, inceleme sonuçlanana kadar bütün işveren kanallarında kapalıdır. Bu engel yalnız günlük ekranıyla sınırlı değildir; işverenin önizleme, küçük resim, doğrudan görüntü bağlantısı, dosya/rapor veya bildirim gibi erişim yollarında da aynı kayıt için uygulanır. Normal görüntünün önizleme/yayın zamanının sayısal değeri seçilmemiştir; önce talep açılabilmesini sağlayan yayın öncesi akış tasarlanacaktır.

Moderasyon talebi açılması çalışma süresini otomatik düşürmez. İnceleme sonucunda görüntüye yapılacak işlem, maskeleme/yayın/saklama davranışı ve olası süre/ücret etkisi ayrıca teknik tasarımda netleştirilir. Öğrenciye doğrudan silme yetkisi veren veya kişisel bilgi talebini otomatik ücretsiz çalışma sonucuna bağlayan davranış eklenmez.

Ekran görüntüleri ve ayrıntılı etkinlik kayıtları 90 gün saklanır. Açık itirazın ilgili kayıtları itiraz sonuçlanana kadar korunur; 90 günlük süre dolması açık itiraz kanıtını silmez. Ödeme ve sözleşme kayıtlarının saklama süreleri ayrı belirlenir.

Kabul kriterleri:

- **AK-10.1:** İlk canlı kapsam Windows/macOS/Linux takip istemcilerini içerir; yalnız web zaman sayacı veya tek OS istemcisi tam takip teslimi sayılmaz. OS sürüm/dağıtım ayrıntıları ayrıca belirlenir.
- **AK-10.2:** Takip, kabul edilmiş beş veri türünü toplar; tuş içeriği/kamera/sürekli video kaydı almaz. Her 10 dakikalık bölümde rastgele screenshot yalnız kullanıcının seçtiği ekrandandır.
- **AK-10.3:** Hareketsizlikte otomatik duraklatma/devam ve offline kayıt/senkronizasyon bulunur; aynı zaman birden fazla ücret kaydına dönüşmez. Hareketsizlik için yeni sayısal değer eklenmez.
- **AK-10.4:** Öğrenci başka öğrencinin kayıtlarına, işveren başka sözleşmenin kayıtlarına erişemez; destek görüntülere yalnız yetkili inceleme kapsamında erişir.
- **AK-10.5:** Öğrenci doğrudan görüntü silemez ve kişisel bilgi talebini işveren görüntüyü görmeden açabilir. Normal yayın zamanı için teknik tasarımda ayrıca değer belirlenir; anında işverene gösterim bu şartı ihlal eder.
- **AK-10.6:** Talep açıldığında ilgili görüntü bütün işveren erişim yollarında moderasyon sonuçlanana kadar engellenir; günlükten gizleyip aynı görüntüyü bağlantı, bildirim, küçük resim veya rapor üzerinden sunmak kabul edilmez.
- **AK-10.7:** Talep açılması tek başına süreyi azaltmaz veya ücreti düşürmez. Moderasyon sonucu/maskeleme/ücret ayrıntısı onaylanmamış teknik tercih olarak açık tutulur.
- **AK-10.8:** Görüntü ve ayrıntılı etkinlik için 90 gün uygulanır; açık itirazın ilgili kayıtları sonuca kadar korunur. Ödeme/sözleşme için aynı süre otomatik olarak varsayılmaz.

### M11 — Mesajlaşma, dosya paylaşımı ve bildirim

Kaynak kararlar: 9, 16–17, 22, 34, 37.

Başvuru veya davet sonrası mesajlaşma açılır; sözleşme öncesi görüşme platform içinde yürür. İlk sürüm yazılı mesaj ve dosya paylaşımı içerir. İşe dahil takım üyeleri kendi sözleşme çalışma alanının iletişimine katılır. Sesli/görüntülü görüşme sonraya bırakılır.

Uygulama içi ve e-posta bildirimleri kullanıcı tercihleriyle sunulur. Teklif, ödeme, teslim ve itiraz bildirimleri önceliklidir. Fonlama başarısızlığı taraflara bildirilir. Bildirim içinde genel bilgi erişimi, özel iş dosyası veya talep edilmiş görüntüye yetkisiz erişim açmaz.

Kabul kriterleri:

- **AK-11.1:** Başvuru/davet ilişkisi oluşmadan sözleşme öncesi görüşme açıldığı varsayılmaz; ilişki oluştuktan sonra platform içi yazılı mesaj/dosya akışı kullanılabilir.
- **AK-11.2:** Sözleşmeye dahil üyenin iletişim yetkisi vardır; genel ziyaretçi veya başka sözleşmenin tarafı mesaj/özel dosyaları göremez.
- **AK-11.3:** Uygulama içi/e-posta kanalları ve kullanıcı tercihleri bulunur; teklif/ödeme/teslim/itiraz ile fonlama başarısızlığı olayları bildirim akışına bağlanır.
- **AK-11.4:** Bildirimler M10'daki görüntü moderasyon engelini veya sözleşme erişim sınırını aşmaz; ses/video ilk sürüm zorunluluğu yapılmaz.

### M12 — Değerlendirme, destek ve yönetim

Kaynak kararlar: 3, 8, 11, 19–22, 27, 39, 45–46, 51–52.

Karşılıklı puan/yorum yalnız sözleşme tarafları tarafından verilir. Yönetim paneli, kabul edilmiş doğrulama yapılandırmaları ve test kredilerinin yanı sıra ilan şikâyetleri, uyuşmazlık, kredi iade talepleri, lider/ödeme alıcısı onayları ve kişisel bilgi görüntü incelemesi için çalışma alanıdır. Ayrıntılı yönetici rolleri ve inceleme sonucunun teknik uygulama biçimi daha sonra tasarlanır; destek için genel veri erişimi varsayılmaz.

Kabul kriterleri:

- **AK-12.1:** Sözleşmesi olmayan kullanıcı puan/yorum bırakamaz; karşılıklı değerlendirme ilgili sözleşmeyle ilişkilidir. Takımın değerlendirme işlemini hangi üye adına yaptığı ayrıca tasarlanır.
- **AK-12.2:** İlan şikâyeti yönetim incelemesine, anlaşmazlık destek çözümüne yönelir; uyuşmazlık ilgili ödeme ve korunacak takip kayıtlarıyla bağlanır.
- **AK-12.3:** Yönetim üniversite e-posta alan adlarını/kategorileri ve test kredilerini yönetebilir; üretim kredisi için seçilmemiş tutar veya yeni disiplin kuralı eklenmez.
- **AK-12.4:** Aktif lider değişikliği işveren/yönetim onayı ve açık ödeme alıcısı kararıyla izlenir; bu kararlar sıradan üye yetkisiyle yürütülmez.
- **AK-12.5:** Kişisel bilgi talepleri yetkili incelemeye ulaşır; moderasyon sonuçlanana kadar ilgili görüntünün işveren erişimi kapalıdır. Kayıt saklamasında AK-10.8 uygulanır; kişisel bilgi talebi tek başına aktif itiraz saklama istisnası olarak varsayılmaz. Kredi iade talebi ile iş bedeli uyuşmazlığı ayrı olaylar olarak sonuçlandırılır.

## 6. Bütün modüllerde korunacak değişmezler

1. Test kapıları ile canlı uygunluk/doğrulama koşulları ayrıdır; test istisnası canlı sürümün doğrulamasız yayımlanması kararı değildir.
2. Kredi, iş bedeli veya kazanç değildir. Bütün krediler süresizdir; aylık haklar önceki bakiyeyi silmez, hesaplar arası kredi aktarımı yoktur.
3. İş bedeli TL ve freelancer komisyonu %10'dur; işverenden iş bedeline ek platform komisyonu alınmaz.
4. Ücretli çalışma ön fonlamaya dayanır; başarısız fonlama yeni ücretli çalışmayı durdurur. İtiraz ilgili ödemeyi bekletir.
5. Saatlik işte takip zorunlu; manuel süre için açık işveren onayı gerekir. Sabit işte takip tercihidir ve ödeme aşama/teslim modelini değiştirmez.
6. Sözleşme ve koşul değişiklikleri karşılıklı kabul gerektirir. Birden fazla işe alım ayrı sözleşme ve erişim sınırları oluşturur.
7. Takım adına başvuru/sözleşme kabulü ve kazanç alımı liderdedir; çalışan üyeler kendi iş iletişimi/teslim/süre işlemlerini yürütür. İç kazanç dağıtımı platform işi değildir.
8. Öğrenci görüntü silemez; kişisel bilgi talebi işveren görünürlüğünden önce açılabilir. İnceleme sonuçlanana kadar ilgili görüntü hiçbir işveren kanalından sunulmaz. Talep, otomatik süre/ücret düşümü değildir.
9. Görüntü/ayrıntılı etkinlik 90 gün; açık itirazın ilgili kanıtı sonuçlanana kadar korunur. Sözleşme/ödeme saklama süresi bununla eşitlenmez.
10. FIRST zorunlu değildir; ilk sürüm bağlantıyla portföy sunar. Otomatik aktarım, ortak giriş ve diğer ürünlerin özel verisine erişim ilk çekirdek gibi varsayılmaz.

## 7. Karar alınmış kapsam içindeki açık uygulama işleri

Bu başlıklar yeni ana ürün özellikleri değildir. Kararların işletilebilmesi için tamamlanacak parametre, teknik sözleşme ve operasyon ayrıntılarıdır; açık kalmaları kabul edilen kapsamın tamamlandığı anlamına gelmez.

- Ücretsiz başlangıç/aylık kredi miktarları, sabit başvuru/ilan/öne çıkarma maliyetleri ve öne çıkarma süresi; kullanılmamış sürenin iade hesabı, satın alınmış kredi iadesinin kesin koşulları ve iş anlaşması sonrasındaki kredi iptal ayrıntıları.
- Doğrulama ve ödeme sağlayıcıları/yöntemleri; üniversite alan adı yönetimi, yıllık yenileme ve mevcut işi tamamlama durumlarının uygulama akışları. Testte bu doğrulamalar canlıya hazırlık aşamasına kadar ertelenir.
- Haftalık dönemin saat dilimi/başlangıç saati, sınır değişikliklerinin dönem etkisi; takımda farklı ücretlerle ön fonlama hesabı, saatlik inceleme ve ödeme/çekim takvimi, çekim alt limiti.
- Normal screenshot önizleme/yayın zamanının değeri, kullanıcıya yayın öncesi kişisel bilgi talebi fırsatı veren akış; bütün işveren erişim yollarında engelin uygulanması; moderasyon sonucu ve maskeleme/süre/ücret etkisi.
- Hareketsizlik süresi; offline kayıt/senkronizasyon ve aynı sürenin tekrar ücretlendirilmesini önleyen teknik sözleşme; Windows/macOS/Linux sürüm/dağıtım desteği ve istemci kurulumu/güncellemesi.
- 90 günlük takip kaydı saklama ile aktif itiraz korumasının teknik uygulanması; ödeme/sözleşme kayıtlarının ayrı saklama süreleri, özel dosya erişimi ve ayrıntılı destek/yönetim yetkileri.
- Takım üyelik yönetimi, kurumsal hesap içi ayrıntılı yetkiler, takımın değerlendirme işlemi ve bildirim tercihlerinin ayrıntılı ekran/sözleşme tasarımı.
- Framework, API, veri modeli, dosya saklama, dağıtım ve ortak giriş entegrasyonu seçimleri. FIRST'teki teknoloji seçimi otomatik STEP teknoloji kararı değildir.

## 8. Karar kapsamı izlenebilirliği

| Kabul edilen kararlar | Karşılayan modül/bölüm |
|---|---|
| 1–6 | M01; aşama ve aktör sınırları |
| 7–9 | M02; M11 ve genel/özel erişim ayrımı |
| 10–14 | M03; takım adına davet/teklif için M05 |
| 15 | M04; M05/M08/M09 koşul kabulü |
| 16–17 | M11 |
| 18–20 | M04/M07/M09; uyuşmazlık desteği M12 |
| 21–22 | M12/M11 |
| 23–27 | M06; kredi iade talebi M12 |
| 28 | M07; sonraki para birimleri aşama tablosu |
| 29–32 | M08/M07 |
| 33–34 | M07/M05; bildirim M11 |
| 35–40 | M05/M01/M06/M07 |
| 41–46 | M10; ücret/inceleme sınırı M08/M09 |
| 47–50 | Ürün sınırları ve aşama tablosu; portföy M02; bağımsız giriş M01 |
| 51–52 | Aşama tablosu; test ödeme/kredi M07/M06; istemciler M10; bütün çekirdek modüller |
| Önceki %10, gerçek para/kredi, iptal iadesi, aşama/14 gün, zorunlu takip ve lider kararları | M04–M10; bütün modüllerdeki değişmezler |

## 9. Teslimin değerlendirilmesi

Bir modül ancak ilgili kabul kriterleri ve yukarıdaki değişmezler birlikte karşılanınca ürün teslimine dahil edilir. Kaynak/diff incelemesi, çalışma zamanı veya canlı ödeme doğrulaması yerine geçmez. Bu planlama turunda uygulama, test, lint, typecheck, tarayıcı/computer use veya canlı işlem çalıştırılmamıştır. Geliştirme görevlerinin kontrol ve teslim kapsamı repo kuralları ile görevdeki açık kullanıcı talimatından belirlenir.
