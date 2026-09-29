# FIRST tamamlama teslimi — 30 Eylül 2026

## Yapılan iş

FIRST kapsamında doğrudan mesaj, ücretsiz Türkiye üniversite e-posta onayı (12 ay), hesap açılışından itibaren GitHub katkı toplamları, isteğe bağlı private toplam paylaşımı, sahibi/kabul edilmiş katkıcısı olunan public repo portfolyosu, PDF/JPG sertifikalar ve tek yönetici paneli uygulandı. Public arama, validation mesajları, public okuma ve moderasyonun katılım/ekip yetki sınırları düzeltildi. Bağımsız kaynak review/verify kapıları geçti. Canlı QA'da görülen yönetici enum etiketleri Türkçeleştirildi ve tekrar incelendi.

## Değişen dosyalar

Backend: accounts/config/projects/teams düzeltmeleri ve yeni profiles/messaging/moderation uygulamaları; frontend: hesap/profil/keşif/mesaj/öğrenci onayı/yönetici ekranları ve API taşıyıcısı; send-machine payload listesi; FIRST kapsam/API/dağıtım belgeleri. Bu run yalnız FIRST dosyalarını teslim eder. Önceden var olan anonim nav etiketi değişikliği ve eşzamanlı STEP çalışmaları teslim kapsamına alınmadı.

## Aktif davranışlar ve yayın

- Backend kaynakları: `22a1c82`, arayüz/kapsam teslimi `3b7497b`; backend release `20260929T230123-3b7497bf3cb5`, sağlıklı. Mevcut yayın akışının Django check, üç migration, PostgreSQL/Redis bağlantısı ve sağlık adımları geçti.
- Doğrulanmış ana hesap exclusive yönetici olarak atandı. FIRST Nginx body limiti yedekli `4m`; config kontrolü/reload/health geçti. Diğer projeler ve kalıcı veri korundu.
- Frontend düzeltmeleri `7ed1f3a` ve `ca4b795`; push hashleri ve Vercel otomatik status success doğrulandı. Türkçe etiketler canonical canlı domainde görüldü.
- Sertifika kuralları kaynakta: PDF/JPG/JPEG, PNG yok; en fazla 10 belge, her belge 2 MiB, toplam 20 MiB. İzole raster önizlemesi; ham dosya indirme yok. Bu sınırlar için dosyalı canlı test henüz yapılmadı.

## Beklenen eklemeler / yanıt bekleyen kontroller

Geliştirme kapsamındaki kaynaklar tamamlandı; bütün canlı senaryoların geçtiği iddia edilmiyor. QA kapısı şu kullanıcı girdileri için açık:

1. Erişilebilir gerçek `.edu.tr` adresi: gönderim, bağlantıyla onay, 12 ay, rozet/filtre ve tek kullanımlık anahtar döngüsü.
2. Sentetik PDF/JPG dosyalarının public profile yüklenmesine onay: yükleme/anonim güvenli önizleme, PNG ve 2 MiB üstü reddi, adet/toplam kota. Dosyalar yalnız yerel temp alanında hazır; henüz seçilmedi/yüklenmedi.
3. İkinci test hesabını kısa süre kısıtlama ve geri açma onayı: mevcut oturum iptali, login reddi, yeniden giriş ve kısıtlı üye/viewer temizleme. Uygulamanın onay penceresi iptal edildi; hesap kısıtlanmadı.

Yeni credential girişi, GitHub'da yeni repo izinleri, gerçek private içerik yayınlama, hesap/kalıcı belge silme ve kapsamlı signup/reset/PR merge senaryoları bu turda yapılmadı. Böyle bir test gereken noktada somut fixture ve işlem anındaki izin/handoff sağlanmalı. Normal DM okunması doğrulandı; eşzamanlı read yarışı, 30+ mesaj sayfalaması ve kota stresi kaynak incelemesiyle sınırlı.

## Manuel kontrol — computer use kanıtı

| Senaryo | Sonuç |
|---|---|
| Yetkili iki Google hesabıyla FIRST giriş | İki hesapta başarılı; mevcut GitHub bağları görüldü |
| Gmail öğrenci isteği / sentetik geçersiz onay anahtarı | Açık format ve geçersiz/kullanılmış/süresi dolmuş anahtar mesajlarıyla reddedildi |
| GitHub katkı yenileme | Başarılı; başlangıç hesabın açılış tarihi; public/private toplamlar ve kapsam sınırlamaları göründü |
| Private toplam tercihi | Kapatılınca public bölüm kayboldu; yeniden açılıp kaydedildi. Repo adları/dosyaları bu bölümde gösterilmedi |
| Portfolyo | Repo sahibi ekleyebildi; sahibi/kabul edilmiş katkıcısı olunmayan repo reddedildi |
| İki hesap DM | Doğrudan konuşma, gönderim, alma, bir okunmamış mesaj, açınca sayacın kalkması ve karşılıklı yanıt başarılı; kendine mesaj reddedildi |
| Yönetici erişimi | Ana hesap yönetici paneli; ikinci hesap erişim reddi; anonim mesaj/yönetici ekranları giriş istedi |
| Şikâyet döngüsü | Sentetik, gerçek ihlal iddiası içermeyen kayıt kuyruğa ulaştı; gerekçeyle işlem gerekmiyor olarak sonuçlandırıldı; otomatik yaptırım olmadı |
| Proje moderasyonu | Test ilanı gizlendi; anonim detay bulunamadı. Geri açılınca aktif/görünür ve public aramada tekrar bulundu |
| Profil moderasyonu | Test profili gizlendi; anonim erişim bulunamadı. Geri açılınca anonim profil göründü; yönetici oturumu korundu |
| Audit | Uygulayan kişi, hedef referansı, tarih ve gerekçe kaydedildi; Türkçe etiketler canlı doğrulandı |
| Standalone ekip | Sentetik ekip oluşturuldu, davet ikinci hesapta gönderildi ve ana hesapta kabul edildi; iki üye listelendi; GitHub izni verilmedi |
| Türkçe kişi/proje araması ve öğrenci filtresi | Doğru kişi/proje sonuçları; onaysız kişiler öğrenci filtresinde görünmedi; arama 500 üretmedi |
| Responsive | Profil 390/320, DM 768/320, audit ve belge düzenleyici 320 gerçek viewport: scrollWidth viewport'a eşit; geçici override resetlendi |
| Konsol | İkinci çalışma sekmesinin yakalanmış error/warn listesi boş; bütün uygulama için eksiksiz hata taraması iddiası değil |

Geri alma durumu: geçici proje/profil gizlemeleri kaldırıldı; kısıtlı hesap sayısı sıfır. Kullanıcının istediği private toplam görünürlüğü açık. Sentetik ekip ve iki test DM'i test kaydı olarak bırakıldı; kalıcı silme yapılmadı. Portfolyo public test reposunu içerir. Screenshot/fixture içerikleri repoya eklenmedi; yalnız güvenli özet tutuldu. Yerel ekran kanıtı: `/tmp/first-qa-proof/messages-two-accounts.jpg`, `/tmp/first-qa-proof/admin-report-complete.jpg`, `/tmp/first-qa-proof/admin-audit-mobile.jpg`.
