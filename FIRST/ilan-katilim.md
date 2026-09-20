# FIRST ilan ve katılım akışı

21 Eylül 2026. Uygulama/test/yayın durumu: [run kaydı](../.orchestrator/runs/first-listing-participation/run.json). Kesin ürün kararları: [kararlar](kararlar.md). API: [katılım sözleşmesi](contracts/participation-api.md).

## İlan oluşturma

Repo başına tek aktif ilan açılır. Projenin üst/alt kategorisi ve aşaması ile birlikte tek bir ihtiyaç seçilir: ekip arkadaşı, contributor, özellik geliştirme veya hata/sorun çözme. Özellik/hata için mevcut durum ve beklenen sonuç gerekir. GitHub Issue yalnız hata/sorun çözme ilanında gerekir; özellik geliştirme ilanında Issue bağlanmaz. Açık reponun son 50 açık Issue kaydı seçim listesinde gösterilir (PR kayıtları dahil edilmez); mevcut kayıt seçilebilir veya yeni Issue oluşturulabilir. Gizli repolarda hata/sorun çözme ilanı açılamaz. GitHub işlemi başarısızsa eksik kurulum açıkça gösterilir; işlem yeniden denenir.

Tek katılım yöntemi seçilir ve yayımlandıktan sonra değiştirilemez. Farklı yöntem için mevcut ilan arşivlenip yeni ilan açılır; aynı repo için iki aktif ilan bulunamaz. İlanın kapanması mevcut GitHub Issue/PR veya erişim yetkilerini kaldırmaz.

## Görünürlük ve katılım ayrı ayarlardır

- Herkese açık ve keşifte: aktif ve başvuruya açık ilan keşifte listelenir.
- Yalnız bağlantıyla: keşifte bulunmaz; bağlantısı olan kişi görebilir.
- Yalnız seçilen kişiler: ilan sahibi, görüntüleme izni verilen kişiler ve geçerli katılım daveti almış kişiler görebilir. Dışarıdan başvuru alınmaz.

Görüntüleme izni repo erişimi sağlamaz. Katılım daveti ayrı bir işlemdir. Private repo ilanının tanıtım metni seçilen görünürlüğe göre paylaşılabilir; GitHub kodu, Issue ve PR verileri için güncel repo erişimi gerekir.

## Başvuru ve davet

Başvuruda açıklama, doğrulanmış e-posta ve bağlı GitHub hesabı gerekir. Aday başvurusunu geri çekebilir; sahibi kabul veya ret kararı verir. Kabul FIRST tarafındaki karardır; repo erişim daveti gönderildiyse GitHub'da davetin kabulü ayrıca gerekir. Repo erişiminin alındığı yalnız davet gönderilmesinden çıkarılmaz.

Sahibin FIRST kullanıcı adına gönderdiği katılım daveti önce FIRST'te kabul edilir; ardından GitHub daveti gönderilir. Kullanıcı GitHub davetini kabul eder ve durumunu yeniler. Görüntüleme iznini kaldırmak GitHub erişimini geri alma işlemi değildir.

PR şartlı katılım yalnız public repoda sunulur. Aday kendi GitHub kimliğine ait PR'ı bağlar. Sahip güncel PR'ı inceleyip belirli commit üzerinden kabul eder. “Kabul et” merge yapar; “Kabul et ve repoya ekle” ayrıca erişim daveti gönderir. PR sonradan değişmişse tekrar inceleme gerekir.

## Otomatik katılım ve GitHub korumaları

GitHub'da “contributor” adında atanabilir dar bir yetki yoktur. Gönderilen collaborator daveti yazma erişimi verir. Otomatik katılımda FIRST repo korumalarını hem ilan açılışında hem erişim daveti gönderirken doğrular. Koruma doğrulanamıyorsa otomatik davet gönderilmez; sahibi GitHub ayarlarını tamamlamalıdır. FIRST bu ayarları kendiliğinden değiştirmez.

Kabul edilen güvenli yapı: mevcut repo dallarında ve tüm etiketlerde güncelleme, silme ve force-push kısıtları; yalnız yönetici bypass yetkisi. Çalışma yeni branch/fork üzerinde PR ile yürür. Repo yazma erişimi branch başına ayrı kullanıcı izni değildir; korumasız çalışma dalları için tam izolasyon garantisi verilmez. Private repolarda kuralları uygulayan GitHub planı da doğrulanmalıdır.

Kurallar mevcut bütün dalları kapsamalıdır. Yeni çalışma dalları eklendikten sonra sonraki otomatik davet, bu dalların korumaları tamamlanana kadar engellenebilir. Yalnız ana dalı korumak, diğer mevcut dalları veya etiketleri korumaz.

## Durum ve bildirimler

Gelen/giden başvurular ve davetler ayrı hesap ekranında yönetilir. Sonuçlar site içinde bildirilir. Açık PR/bağlı Issue verileri açık yenileme işlemiyle alınır; yayınlanmış proje metni GitHub'dan otomatik güncellenmez. Contributor istatistikleri ve sohbet bu aşamada yoktur.

İlanı başvurulara kapatma, görünürlük ve arşivleme ayrıdır. Eski başvurular kapanıştan sonra değerlendirilebilir. Başvuru kabulü, Issue kapanması veya PR merge işlemi ilanı otomatik kapatmaz.
