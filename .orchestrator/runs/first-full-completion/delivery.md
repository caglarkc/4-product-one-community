# FIRST tamamlama teslimi — 30 Eylül 2026

## Yapılan iş

FIRST kapsamında doğrudan mesaj, ücretsiz Türkiye üniversite e-posta onayı (12 ay), hesap açılışından itibaren GitHub katkı toplamları, isteğe bağlı private toplam paylaşımı, sahibi/kabul edilmiş katkıcısı olunan public repo portfolyosu, PDF/JPG sertifikalar ve tek yönetici paneli uygulandı. Public arama, validation mesajları, public okuma ve moderasyonun katılım/ekip yetki sınırları düzeltildi. Bağımsız kaynak review/verify kapıları geçti. Canlı QA'da görülen yönetici enum etiketleri Türkçeleştirildi ve tekrar incelendi.

Kullanıcının öğrenci e-postası dışındaki kalan testleri yetkilendirdiği devam turunda belge yükleme/kotaları, mesaj geçmişi/hız sınırı/okunmamış durumu, hesap kısıtlama/geri açma ve gerçek GitHub PR birleştirme senaryoları canlıda doğrulandı. Uygulama onayları hedefi ve sonucu gösteren, başlangıçta işaretlenmemiş kutu ile son onay düğmesini gerektiren ortak sayfa içi bileşene taşındı. Onay zorunluluğu korundu; kaynak bağımsız incelemeden geçti. Kısıtlı ekip sahibinin 404 mesajı Türkçeleştirildi. Yeni kayıt ve şifre sıfırlama tam döngüleri açık olduğu için bütün testlerin tamamlandığı iddia edilmiyor.

## Değişen dosyalar

Backend: accounts/config/projects/teams düzeltmeleri ve yeni profiles/messaging/moderation uygulamaları; frontend: hesap/profil/keşif/mesaj/öğrenci onayı/yönetici ekranları ve API taşıyıcısı; send-machine payload listesi; FIRST kapsam/API/dağıtım belgeleri. Devam turundaki frontend düzeltmeleri `components/ui/confirmation-action.tsx`, `administration.tsx`, `teams.tsx` ve `profile-extension.tsx` dosyalarını kapsar. Bu run yalnız FIRST dosyalarını teslim eder. Önceden var olan anonim nav etiketi değişikliği ve eşzamanlı STEP çalışmaları teslim kapsamına alınmadı.

## Aktif davranışlar ve yayın

- Backend kaynakları: `22a1c82`, arayüz/kapsam teslimi `3b7497b`; backend release `20260929T230123-3b7497bf3cb5`, sağlıklı. Mevcut yayın akışının Django check, üç migration, PostgreSQL/Redis bağlantısı ve sağlık adımları geçti.
- Doğrulanmış ana hesap exclusive yönetici olarak atandı. FIRST Nginx body limiti yedekli `4m`; config kontrolü/reload/health geçti. Diğer projeler ve kalıcı veri korundu.
- Frontend düzeltmeleri `7ed1f3a` ve `ca4b795`; push hashleri ve Vercel otomatik status success doğrulandı. Türkçe etiketler canonical canlı domainde görüldü.
- Devam turundaki sayfa içi onay bileşeni `9de191dbce3513fa35ad69b546a281b6e1f69235`, ekip 404 mesajı `d447214e4e83f67ffee42e076f3617c8a5f45ed2` ile `origin/main` hedefine pushlandı; uzak hashler ve Vercel otomatik success durumu doğrulandı. Yeni onaylar ve Türkçe 404 mesajı canlı arayüzde görüldü. Bu frontend değişiklikleri backend rebuild gerektirmedi; backend release değişmedi.
- Sertifika kuralları: PDF/JPG/JPEG, PNG yok; en fazla 10 belge, her belge 2 MiB, toplam 20 MiB. İzole raster önizlemesi; ham dosya indirme yok. Canlıda tam 2 MiB boyutunda 10 sentetik belge toplam 20 MiB olarak kabul edildi; anonim güvenli raster önizlemeleri görüntülendi. PNG ve 2 MiB + 1 bayt dosya istemcide API çağrısından önce reddedildi; 10 belgede yeni yükleme formu devre dışı kaldı.

## Beklenen eklemeler / kalan kontroller

Geliştirme kapsamındaki kaynaklar tamamlandı; bütün canlı senaryoların geçtiği iddia edilmiyor. Önceki turdaki belge yükleme ve geçici hesap kısıtlama onayları kullanıcı tarafından devam turunda verildi; bu senaryolar aşağıdaki canlı sonuçlarla tamamlandı. Önceki result artefactları tarihsel kanıt olarak değiştirilmedi.

Devam QA sonucu `results/live-qa-continuation-2026-09-30T00-12-47-000Z.json` dosyasında **blocked** olarak kaydedildi. Bekleyen işlem onayları, yeni credential handoff ve yeni kayıt test adresi seçimi açık kaldı; öğrenci e-postası kullanıcının açık istisnasıdır.

1. Gerçek `.edu.tr` adresine gönderim, bağlantıyla onay, 12 ay, rozet/filtre ve tek kullanımlık anahtar döngüsü kullanıcının son talimatıyla bu test turunun dışında bırakıldı.
2. Şifre sıfırlama e-postasının Gmail'e ulaşması ve bağlantının sıfırlama formunu açması doğrulandı. Yeni credential girişi kullanıcıya handoff bekliyor; başarılı sıfırlama, tek kullanımlılık ve sıfırlama sonrasındaki oturum iptali henüz canlıdan doğrulanmadı.
3. Yeni üyelikte boş zorunlu alanlar ve geçersiz e-posta native form validasyonuyla reddedildi. Somut test adresi seçimi kullanıcıya soruldu; henüz yanıt yok. Gerçek yeni hesap oluşturma ve doğrulama döngüsü tamamlanmadı.
4. Gerçek GitHub PR birleştirme ve ikinci hesapta `caglarkc/Data-Structures-Algorithms` reposunu “Kabul edilmiş katkıcı” rolüyle portfolyoya ekleme başarılı; aynı repo ve rol ikinci hesabın public profilinde de doğrulandı. FIRST'te ilanının bulunması portfolyoya eklemeyi engellemez. Değişen gerçek ve geçerli PR head SHA ile gönderim arasındaki dar yarış canlıda tetiklenmedi; değişiklik sonrası onayın sıfırlanması ve geçersiz SHA'da düğmenin kapanması kontrol edildi.
5. Public profildeki 10 sentetik QA belgesinin kalıcı kaldırılması için istenen işlem onayı henüz yanıtlanmadı; belgeler toplam 20 MiB olarak duruyor. Hesap veya belge silinmedi.
6. İkinci hesabın public Vehicle projesine başvurusu ve ana hesabın bekleyen başvuruyu görmesi doğrulandı. Gerçek yeni GitHub erişimi verecek kabul işlemi için somut işlem anı onayı soruldu; henüz yanıt yok. Bu başvuru bekliyor ve yeni GitHub izni verilmedi.

Dar GET/read yarışının deterministik eşzamanlı tetiklenmesi UI üzerinden doğrulanmadı; ID'ye bağlı monoton okundu sınırı kaynak incelemesiyle doğrulandı. Yeni mesajın eski açık konuşmada kendiliğinden okunmuş sayılmaması, inbox ve mesaj yenilemesiyle canlı kontrol edildi. 20 MiB üstüne çıkarken diğer iki sınırı geçerli tutan ayrı bir senaryo mümkün değil: en fazla 10 belge × her biri en fazla 2 MiB zaten en fazla 20 MiB eder. İstemcide reddedilen dosya türü/boyutu örnekleri backend reddi olarak sunulmaz; backend kontrolleri kaynak incelemesi kapsamındadır.

## Manuel kontrol — computer use kanıtı

| Senaryo | Sonuç |
|---|---|
| Yetkili iki Google hesabıyla FIRST giriş | İki hesapta başarılı; mevcut GitHub bağları görüldü |
| Gmail öğrenci isteği / sentetik geçersiz onay anahtarı | Açık format ve geçersiz/kullanılmış/süresi dolmuş anahtar mesajlarıyla reddedildi |
| GitHub katkı yenileme | Başarılı; başlangıç hesabın açılış tarihi; public/private toplamlar ve kapsam sınırlamaları göründü |
| Merge sonrası katkı yenileme | İkinci hesapta “Katkı verileri güncellendi.” sonrası public toplamlar 1 birleştirilmiş PR, 1 commit ve 1 proje gösterdi; başlangıç 21.09.2026 hesap açılış tarihi. Aynı public toplamlar ikinci hesabın public profilinde görüldü; private toplam bölümü görünmedi. GitHub indeks/kapsam sınırlamaları geçerli; private toplamlar bu kayda alınmadı |
| Private toplam tercihi | Kapatılınca public bölüm kayboldu; yeniden açılıp kaydedildi. Repo adları/dosyaları bu bölümde gösterilmedi |
| Portfolyo | Repo sahibi ekleyebildi; sahibi/kabul edilmiş katkıcısı olunmayan repo reddedildi |
| Kabul edilmiş katkıcı portfolyosu | Gerçek PR merge sonrasında ikinci hesap `caglarkc/Data-Structures-Algorithms` reposunu ekleyebildi; “Repo profil vitrininize eklendi.” ve “Kabul edilmiş katkıcı” rolü görüldü. Repo ve rol ikinci hesabın public profilinde de doğrulandı. Bu FIRST profil işlemi yeni GitHub erişimi vermedi |
| İki hesap DM | Doğrudan konuşma, gönderim, alma, bir okunmamış mesaj, açınca sayacın kalkması ve karşılıklı yanıt başarılı; kendine mesaj reddedildi |
| Belge yükleme ve public önizleme | 10 adet tam 2 MiB PDF/JPG toplam 20 MiB kabul edildi; anonim raster önizlemeleri görüntülendi; 11. yükleme formu 10 belgede engellendi |
| Belge reddi ve hız sınırı | PNG ve 2 MiB + 1 bayt dosya istemcide API'den önce reddedildi. 5 yükleme/dakika sınırında fazla deneme reddedildi; seçili dosya korundu, bekleme sonrası yeniden deneme başarılı |
| Mesaj sayfalaması | 32 mesajlı yenilenmiş konuşmada son 30 mesaj ve eski mesajları yükleme kontrol edildi; tüm 32 mesaj farklı kimliklerle, kronolojik ve duplicatesız göründü |
| Mesaj gönderim hız sınırı | 30 QA gönderimi ve önceki iki mesaj toplam 32 kayıt oluşturdu. Aynı sınır penceresindeki sonraki gönderim reddedildi; composer korundu. 60 saniye sonrası yeniden gönderim başarılı, toplam 33 kayıt |
| Yeni mesaj ve okunmamış durumu | Sonraki yeni mesajla toplam 34 kayıt oldu; eski açık konuşmada yeni içerik görünmedi. Yalnız inbox yenilendiğinde bir okunmamış mesaj kaldı; mesajlar yenilendiğinde yeni mesaj göründü ve sayaç sıfırlandı |
| Yönetici erişimi | Ana hesap yönetici paneli; ikinci hesap erişim reddi; anonim mesaj/yönetici ekranları giriş istedi |
| Şikâyet döngüsü | Sentetik, gerçek ihlal iddiası içermeyen kayıt kuyruğa ulaştı; gerekçeyle işlem gerekmiyor olarak sonuçlandırıldı; otomatik yaptırım olmadı |
| Proje moderasyonu | Test ilanı gizlendi; anonim detay bulunamadı. Geri açılınca aktif/görünür ve public aramada tekrar bulundu |
| Profil moderasyonu | Test profili gizlendi; anonim erişim bulunamadı. Geri açılınca anonim profil göründü; yönetici oturumu korundu |
| Audit | Uygulayan kişi, hedef referansı, tarih ve gerekçe kaydedildi; Türkçe etiketler canlı doğrulandı |
| Standalone ekip | Sentetik ekip oluşturuldu, davet ikinci hesapta gönderildi ve ana hesapta kabul edildi; iki üye listelendi; GitHub izni verilmedi |
| Geçici hesap kısıtlama ve geri açma | İkinci hesabın kimliği temiz ayrı browser bağlamlarında doğrulandı. Kısıtlama eski oturumu kapattı; fresh Google giriş reddedildi. Public profil ve bu hesaba ait ekip 404 verdi, yeni DM devre dışı kaldı. Geri açınca eski oturum giriş yapmış duruma dönmedi; yeni Google giriş başarılı, kısıtlı hesap toplamı sıfır |
| Kısıtlı üye/viewer temizliği | Ana hesap ikinci hesabın sentetik ekip üyeliğini ve public test ilanının FIRST görüntüleme iznini kısıtlama sırasında kaldırabildi. İşlemler GitHub erişimi vermedi; hesap yeniden aktif hale getirildi |
| Sayfa içi işlem onayı | Başlangıçta işaretlenmemiş onay kutusu ve kapalı son düğme; Vazgeç/Escape, odağın geri dönmesi, gerekçe değişince onayın sıfırlanması ve işlem sırasında disabled durumu canlı kontrol edildi. Gerçek suspend/reactivate bu onaylarla başarılı |
| Belge kaldırma onayının iptali | Ana hesabın ilk QA belgesinde hedef başlık ve kalıcı kaldırma sonucu gösterildi; işaretlenmemiş kutuda son düğme kapalıydı, kutu işaretlenince açıldı. Escape ile onay kapandı ve odak geri döndü; 10/10 belge korundu, DELETE yapılmadı |
| Ekip 404 mesajı | Kısıtlı ekip sahibinde Türkçe “Ekip bulunamadı veya görüntülenemiyor.” mesajı canlı doğrulandı; diğer hata ve retry davranışları kaynakta korundu |
| Şifre sıfırlama e-postası | FIRST reset e-postası Gmail'de görüldü; 30 dakikalık bağlantı sıfırlama formunu açtı. Yeni credential girilmedi; tam döngü pending |
| Yeni üyelik formu | Boş zorunlu alanlar ve geçersiz e-posta native validasyonu başarılı; gerçek yeni kayıt tamamlanmadı |
| Gerçek GitHub PR döngüsü | İkinci GitHub hesabıyla public fork, QA dalı ve sekiz satırlık dokümantasyon değişikliği üzerinden [PR #1](https://github.com/caglarkc/Data-Structures-Algorithms/pull/1) oluşturuldu. FIRST başvurusu üzerinden sahibi gerçek head SHA'yı aldı; onaylanmamış merge düğmesi kapalıydı, SHA geçersiz hale getirilince onay sıfırlandı ve düğme kapandı. Doğru SHA ile onaylı merge sonrası FIRST “Kabul edildi · PR birleştirildi”, yenilenmiş GitHub sayfası “Merged” gösterdi. Merge-only işlem yeni GitHub erişimi vermedi |
| Public proje başvurusu | İkinci hesap public Vehicle projesine başvurdu; ana hesabın gelen başvurularında bekleyen kayıt görüldü. Yeni GitHub erişimi verecek kabul için işlem anı onayı henüz yanıtlanmadı; kabul veya yeni izin verilmedi |
| Mevcut GitHub erişimini yenileme | Ana hesap mevcut Sport katılımında yenileme işlemini yaptı; “Kabul edildi · GitHub erişimi aktif” durumu korundu. Bu sonuç mevcut erişimin durum yenilemesidir; yeni GitHub erişimi verildiği iddia edilmez |
| Türkçe kişi/proje araması ve öğrenci filtresi | Doğru kişi/proje sonuçları; onaysız kişiler öğrenci filtresinde görünmedi; arama 500 üretmedi |
| Responsive | Profil 390/320, DM 768/320, audit ve belge düzenleyici 320 gerçek viewport: scrollWidth viewport'a eşit; geçici override resetlendi |
| Konsol | İkinci çalışma sekmesinin yakalanmış error/warn listesi boş; bütün uygulama için eksiksiz hata taraması iddiası değil |

Geri alma durumu: geçici proje/profil gizlemeleri kaldırıldı; ikinci hesap tekrar aktif ve kısıtlı hesap sayısı sıfır. Kullanıcının istediği ana hesaptaki private toplam görünürlüğü açık; ikinci hesapta kapalı kalır ve public profilde private bölüm yoktur. İki sentetik QA ekibi ve toplam 34 test DM'i test kaydı olarak bırakıldı. Kısıtlı hesapla ilişkilendirilen sentetik üyelik ve FIRST viewer izni kaldırıldı; GitHub erişimi verilmedi. 10 sentetik belge public profilde toplam 20 MiB olarak duruyor; kalıcı belge veya hesap silme yapılmadı. Ana hesabın portfolyosu public test reposunu, ikinci hesabın portfolyosu kabul edilmiş katkıcı olarak test edilen public repoyu içerir. Sentetik GitHub PR birleştirildi; QA fork/dal/dokümantasyon dosyası ve kabul edilmiş FIRST başvurusu korunuyor, bunlar için cleanup yapıldığı iddia edilmiyor. Vehicle başvurusu yeni GitHub erişimi verilmeden bekliyor; mevcut Sport erişimi yalnız yenilendi. Şifre sıfırlama formunda yeni credential girilmedi/değiştirilmedi. Screenshot/fixture içerikleri repoya eklenmedi; yalnız güvenli özet tutuldu. Tarihsel yerel ekran kanıtı: `/tmp/first-qa-proof/messages-two-accounts.jpg`, `/tmp/first-qa-proof/admin-report-complete.jpg`, `/tmp/first-qa-proof/admin-audit-mobile.jpg`.

Kontrol yöntemi: kaynak/diff incelemesi ve kullanıcı tarafından açıkça istenen canlı computer use. Bu devam turunda test suite, lint, typecheck veya yerel build çalıştırılmadı. İlk yayının mevcut deployment kontrol sonuçları, canlı UI gözlemlerinden ayrı tutulur.
