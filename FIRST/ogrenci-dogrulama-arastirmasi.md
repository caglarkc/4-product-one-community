# FIRST — Öğrenci doğrulaması araştırma notu

Araştırma: 16 Eylül 2026. Kayda aktarım: 17 Eylül 2026. Fiyatlar bu görüşmedeki resmî kaynak bulgularıdır; satın alma sırasında yeniden doğrulanmalıdır. Hiçbir servis seçilmedi, iletişim/abonelik/ödeme yapılmadı.

## Amaç ve ayrım

- Üniversite öğrencilerine ileride profil öne çıkarma ve site içi avantajlar sağlama niyeti kabul edildi; avantajların ayrıntıları açık.
- Kullanıcı, okul e-postasına erişen mezunların öğrenci sayılmasını istemiyor ve ücretli aktif öğrenci doğrulamasının değerlendirilmesini istedi.
- Üniversite e-postasına bağlantı gönderip doğrulamak yalnızca o adrese erişimi kanıtlar; aktif öğrencilik kanıtı değildir. E-postayı düzenli yeniden doğrulamak bu farkı ortadan kaldırmaz.
- Aktif statü için güncel kurum verisi veya doğrulanabilir güncel belge kontrolü gerekir. Ücretli servis kullanımı, her mezunun kesin olarak ayırt edileceği garantisi değildir.

## Konuşulan yöntemler (seçilmedi)

- Üniversiteye ait tanımlı alan adları ve tek kullanımlık e-posta bağlantısıyla kendi doğrulamamız; rozet “Üniversite e-postası doğrulandı” olabilir. Kullanıcı bunun mezunları ayıramayacağını belirtti; tek başına aktif öğrenci statüsü için kabul edilmedi.
- Güncel öğrenci belgesini kendimiz inceleme: manuel iş yükü var; seçilmedi.
- Harici öğrenci doğrulama servisi: araştırılması istendi; sağlayıcı seçilmedi.
- Aktif öğrenci statüsünü süreli tutup akademik yıl bazında yenileme önerildi; süre henüz onaylanmadı.
- Üniversite e-postasını ana giriş e-postasından ayrı ekleme önerildi; nihai ekran/veri modeli seçilmedi.

## E-posta gönderimi maliyeti

Resend araştırma tarihinde ücretsiz planda aylık 3.000/günlük 100 e-posta, Pro başlangıcında aylık 20 USD/50.000 e-posta gösteriyordu. Bu öğrenci doğrulama hizmeti değil, mesaj gönderim hizmetidir. Hesap doğrulama ve şifre sıfırlama gönderimleri de kotayı kullanır. Resend seçilmedi.

Kaynaklar: [fiyat](https://resend.com/pricing), [kotalar](https://resend.com/docs/knowledge-base/account-quotas-and-limits).

## Ücretli hizmet karşılaştırması

| Hizmet | Araştırma sonucu | Durum |
|---|---|---|
| SheerID | Açık sabit fiyat yok, özel teklif gerekiyor. Türkiye'ye yönelik kampanyalar mevcut; bu her Türk üniversitesinin aynı yöntemle desteklendiği anlamına gelmez. Güncel öğrenci belgesi talep edilebiliyor. API/webhook entegrasyonu mevcut. | İlk teklif adayı olarak önerildi; seçilmedi. |
| Student Beans Connect | Bölgesel self-service sayfasında US/Canada için aylık 200 USD veya yıllık 1.800 USD. İndirim/satış odaklı; bazı paket anlatımlarında komisyon da var. Türkiye'deki ücretsiz topluluğa uygulanacak toplam fiyat ve kapsam teyitsiz. | Alternatif, teklif gerekiyor. |
| VerifyPass | Aylık 49 USD; ilk 49 olumlu doğrulama dahil, sonrası kademeli işlem ücreti. Standart öğrenci kapsamı ABD, İngiltere, Kanada, Avustralya. | Türkiye için mevcut standart paket önerilmedi. |

UNiDAYS de araştırmada görüldü; güncel yıl belgesi/kurum portalı gibi yolları var. FIRST için ticari fiyat ve Türkiye kapsamı teyit edilmedi, seçilmedi.

## SheerID için önerilen teklif soruları

- Aylık 100, 500 ve 1.000 doğrulamada toplam maliyet.
- Türkiye'de desteklenen üniversiteler ve kurum başına aktif öğrencilik kontrol yöntemi.
- Mezun e-posta erişimini aktif öğrenci kabulünden ayıran koşullar.
- Türkçe ve e-Devlet öğrenci belgesi kabulü (teyit edilmedi).
- Kurulum, minimum taahhüt, başarısız deneme ve yeniden doğrulama bedelleri.
- Ücretsiz toplulukta öğrenci rozeti/avantajları için hizmet verilip verilmediği.

Önerilen entegrasyon: kullanıcı doğrulama akışını başlatır, sağlayıcının ekranını tamamlar; backend sonucu sağlayıcıdan teyit ederek hesaba statü ekler. Statünün süresi henüz seçilmedi. Sağlayıcı sonucu kullanıcı hesabıyla eşleştirme ve belge saklama tasarımı henüz yapılmadı.

## Kaynaklar

- [SheerID fiyatlandırma](https://www.sheerid.com/pricing/)
- [SheerID Türkiye kampanyaları](https://shop.sheerid.com/countries/turkey/)
- [SheerID öğrenci koşulları](https://verify.sheerid.com/student-faq/?pid=5d5ece176b2d3c2233ed8346)
- [SheerID webhook entegrasyonu](https://developer.sheerid.com/tutorials/verifications/webhooks)
- [Student Beans bölgesel fiyatlar](https://partner.studentbeans.com/verification/self-service/pricing/options/)
- [Student Beans Connect paket açıklaması](https://partner.studentbeans.com/verification/student-verification/connect/connect-demo-video/)
- [VerifyPass fiyat](https://verifypass.com/verification/pricing)
- [VerifyPass öğrenci kapsamı](https://verifypass.com/verification/communities/edu)
- [UNiDAYS doğrulama desteği](https://www.myunidays.com/US/en-US/support)
