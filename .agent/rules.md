# Ortak proje kuralları

- Ürün fikri, özellik önerisi ve kesin uygulama kararını ayır. PATH son ürün ve kapsamı belirsizdir.
- Mevcut ürün belgelerini kullanıcı istemeden genişletme. Yeni teknik kararları ilgili run'ın `decisions`/`assumptions` alanlarında kaydet.
- Tek ürün odağında sınırları o ürünün README ve karar belgelerinden kontrol et. Ürünler arası proje, katkı, ücretli iş ve mentorluk ilişkileri göreve dahilse `.agent/skills/cross/product-boundaries/SKILL.md` kullan.
- Ortak dosyaları tek writer yönetir. Ürünler arası işlerde integration düğümü oluştur; veri/API/auth işleri mevcut kalite kapılarını kullanır.
- Orchestrator mekanizmasını geliştirme, yeni framework veya sabit agent kadrosu ekleme. Yapı Immense'den uyarlanmıştır.
- FIRST için Django/DRF backend ve Next.js frontend uygulaması ve dağıtım altyapısı vardır. Gerçek kaynakları ve manifestleri esas al; diğer ürünlerin uygulama durumunu varsayma.
- Yerel kontrolleri görev ve platform izinleri kapsamında çalıştır. Immense'in uzak Docker/Flutter çalışma kısıtları burada varsayılmaz.
- Run/result/event dosyalarına token, kişisel veri veya ekran görüntüsü içeriği koyma; güvenli özet ve referans kullan.

## Frontend geliştirme aşaması

18 Eylül 2026 kararıyla FIRST tasarım aşaması açılmıştır. `FIRST/tasarim-dili.md` içindeki onaylı renk/tema dili, merkezi token'lar ve ortak UI bileşenleri mevcut ve yeni FIRST sayfalarında kullanılır. Referans görselin yerleşimi ve örnek özellikleri kapsam onayı değildir. STEP, INTO ve PATH için ayrı karar verilene kadar işlev ve sade yerleşim önceliği korunur. Frontend işlerinde `.agent/skills/frontend/frontend-implementation/SKILL.md` uygulanır.

## Git Teslim Protokolü

Kullanıcının kalıcı talimatı: **Dosya değişikliği yapılan her görev sonunda, ilgili kontroller tamamlandıktan sonra değişiklikleri anlamlı commit'lerle kaydet ve pushla.** Her görevde yeniden izin isteme. Kullanıcı o görev için commit/push istemediğini belirtirse veya farklı branch seçerse bu talimatı uygula.

- Yalnız göreve ait, kabul edilen dosyaları açık yollarla stage et; kullanıcının ilgisiz değişikliklerini commit'e katma.
- Birbiriyle ilişkili değişiklikleri bağımsız incelenebilir Conventional Commit'lere ayır; mesajda somut değişikliği anlat. Dosya başına yapay commit üretme.
- Mevcut branch'i ve kullanıcının hedefini koru. Upstream varsa oraya; yoksa doğrulanmış `origin` remote'unda aynı branch adına pushla. Yeni branch gerekiyorsa `codex/` öneki kullan.
- Çoklu agent işlerinde writer/review/verify alt agentları bağımsız push yapmaz; gerekli kalite kapıları tamamlanınca entegrasyon sahibi ana agent toplu teslim yapar.
- Dosya değişmediyse boş commit üretme. Gerekli kontrol başarısızsa görevi tamamlandı sayma; düzelt veya engeli açıkça bildir.
- Force-push yapma. Push reddedilirse remote durumunu incele; güvenle çözülemeyen çatışma veya izin sorununu raporla. Platform izinleri bu talimattan ayrı kalır.
- Teslimde commit hash'lerini, push hedefini ve sonucu belirt. Push sonrası remote branch hash'ini doğrula; başarısız push'ı başarılı gösterme.

## FIRST yayın teslim protokolü

18 Eylül 2026 kalıcı kullanıcı talimatı: FIRST backend değişikliğinde, kullanıcı o görev için açık istisna belirtmedikçe, gerekli test/review kontrollerinden sonra commit ve GitHub push yap; root SSH ile doğrulanmış sunucudaki `/root/first-backend` checkout'unda `git pull --ff-only` çalıştır; push edilen commit'i doğrula ve bu kaynaklardan Docker backend image'ını yeniden build edip servisi ayağa kaldır. Her görevde yeniden onay isteme. Sunucu adresini kök `.env` içinden oku; gizli değerleri çıktıya yazma.

- Standart işlem ve mevcut altyapı `FIRST/deployment.md` ve `./send-machine` içindedir. Uzak checkout kirliyse veya commit farklıysa değişiklikleri ezme; sebebi çözmeden dağıtım yapma.
- FIRST PostgreSQL/Redis kalıcı verilerini, sunucuya özgü anahtarları ve diğer projeleri koru. Mevcut yedekleme, migration, rollback ve sağlık kontrollerini kullan. Başarısız dağıtımı başarılı sayma; durumu açıkça bildir.
- FIRST frontend push sonrası Vercel otomatik build/deploy alır. Ek yerel üretim build'i veya manuel Vercel deployment başlatma; ilgili test/lint/typecheck kontrollerini çalıştır, Vercel sonucunu ve canlı entegrasyonu doğrula.
- Yalnız belge/skill değişikliğinde backend rebuild gerekmez. Kullanıcının göreve özel istisnası önceliklidir; platform izinleri ayrı kalır. Teslimde push edilen commit, uzak backend release/sağlık durumu ve frontend dağıtım sonucu belirtilir.
