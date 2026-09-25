# FIRST — ilk sürüm açıkları ve kompakt arayüz

## Yapılan iş

Kullanıcının onayladığı bağımsız ekip sistemi, private dosya vitrini ve public GitHub Issue görev kapsamı backend/frontend olarak tamamlandı. Frontend alt agent ortak görünümü kompaktlaştırdı; ana agent katmanları birleştirdi. Ayrı reviewer kaynak incelemesiyle yetki, görünürlük, idempotency, sayfalama ve entegrasyonu kabul etti. İlk başarısız inceleme ve düzeltmeler run geçmişinde korunur.

## Değişen dosyalar

Yeni `FIRST/backend/{teams,showcase,tasks}` modelleri, API'leri ve üç migration; ilgili `FIRST/contracts/*-api.md`; `FIRST/frontend/src/components/{teams,showcase,tasks}.tsx`, ekip/görev route'ları; ortak token/CSS/navigasyon/API, proje detayı ve hesap silme koruması. Docker bağımlılıkları ve `send-machine` kaynak listesi güncellendi. Ürün kararları, README'ler, bağlam haritaları ve eski run kayıtları gerçek teslim kanıtlarıyla uzlaştırıldı.

## Aktif davranışlar

- Ekip keşfi, oluşturma, sahip/yönetici/üye rolleri, başvuru/davet, sahiplik devri, proje bağlama, kaydetme, ayrılma/kapatma; üyelik GitHub erişimi vermez. Liste koleksiyonları sayfalıdır.
- Private repo sahibi en fazla üç seçili dosyayı önizleyip onayla yayımlar/değiştirir/kaldırır. Metin/Markdown/CSV 1 MiB, PNG/JPEG/WebP/PDF 10 MiB, toplam 20 MiB. Yayımlanan sürüm ilan görünürlüğünü izler; ham indirme yoktur. PDF ilk 6 sayfa, CSV ilk 200 satır / 30 sütun, görsel ilk kare önizlemesi; kesme açıkça gösterilir.
- Public projelerin Issue görev keşfi, bağlama/oluşturma ve elle durum yenileme; atama/rezervasyon/private görev yoktur. Belirsiz oluşturma sonucu kalıcı işlem kimliğiyle uzlaştırılır, kör tekrar POST edilmez.
- Daha dar 1280px kabuk, 14px gövde, 22–28px başlıklar, 16–20px paneller; 44px kontroller korunur. Hesap bağlantıları tek menüde.

## Beklenen eklemeler

Bu onaylı uygulama kapsamından açık özellik kalmadı. Mesajlaşma, öğrenci doğrulaması, katkı istatistikleri, ayrıntılı profil/sertifika vitrini ve şikâyet yönetim paneli bilinçli ertelenmiştir. Bunlar tamamlandı sayılmaz.

## Manuel kontrol

Kaynak/diff incelemesi ve orchestrator kayıt doğrulaması yapıldı. Kullanıcı tercihine göre test, lint/typecheck, tarayıcı/computer-use veya ek yerel build çalıştırılmadı. Gerçek GitHub daveti/ikinci hesap kabulü/Issue oluşturma/PR merge uçtan uca doğrulanmadı. PDF/görsel dönüştürücünün çalışma zamanı uyumluluğu ve container bellek payı denenmedi; PDF sistem fontu ikamesi sandbox nedeniyle sınırlıdır. Görsel görünüm tarayıcıda doğrulanmadı.

Uygulama commit’i `de95d27`; kapsam/teslim kaydı commit’i `80dfbcb82b74a495864bb89c16bc0a392fd0f00c`. İkisi origin/main’e gönderildi; uzak branch hash’i doğrulandı. `./send-machine` aynı 80dfbcb commit’ini uzak checkout’ta fast-forward pull ile aldı ve `20260925T084216-80dfbcb82b74` release’ini yayımladı. Docker build, Django system check, showcase/tasks/teams initial migration’ları, PostgreSQL/Redis bağlantıları ve container/HTTP sağlık kontrolü başarılı. Kalıcı veriler korundu. Vercel 80dfbcb otomatik frontend dağıtımını success olarak bildirdi. Bu yayın kontrolleri kullanıcı akışlarının uçtan uca doğrulanması değildir.

Sonraki yalnız-belge commit’i bu sonuçları ve kapatılan integration kaydını taşır; backend kaynakları aynı kaldığından yeniden build gerekmez.

Kayıt sınırı: integration dahil tüm güncel işler ve kalite kapıları tamamlandı. İlk başarısız inceleme, skill gereği silinmedi veya başarılı diye yeniden etiketlenmedi. Mevcut orchestrator hesaplayıcısı düzeltilmiş revision olsa da tarihsel `failed` düğümü nedeniyle run toplamını `blocked` gösterir; bu bir açık ürün işi veya giderilmemiş bulgu değildir. Orchestrator mekanizması bu ürün görevi kapsamında değiştirilmedi.
