# Ortak proje kuralları

- Ürün fikri, özellik önerisi ve kesin uygulama kararını ayır. PATH son ürün ve kapsamı belirsizdir.
- Mevcut ürün belgelerini kullanıcı istemeden genişletme. Yeni teknik kararları ilgili run'ın `decisions`/`assumptions` alanlarında kaydet.
- Tek ürün odağında sınırları o ürünün README ve karar belgelerinden kontrol et. Ürünler arası proje, katkı, ücretli iş ve mentorluk ilişkileri göreve dahilse `.agent/skills/cross/product-boundaries/SKILL.md` kullan.
- Ortak dosyaları tek writer yönetir. Ürünler arası işlerde integration düğümü oluştur; veri/API/auth işleri mevcut kalite kapılarını kullanır.
- Orchestrator mekanizmasını geliştirme, yeni framework veya sabit agent kadrosu ekleme. Yapı Immense'den uyarlanmıştır.
- Repo şu anda fikir belgelerinden oluşur. Olmayan API, veritabanı, UI, deploy veya test komutlarını mevcutmuş gibi yazma.
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
