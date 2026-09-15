# Teknoloji durumu ve entegrasyon ihtiyaçları

## Kesin durum

Repo ürün fikri belgelerinden oluşuyor. Ürün frontend/backend framework'ü, dil, veritabanı, kimlik servisi, ödeme/görüşme/AI sağlayıcısı ve hosting seçilmedi. Node.js yalnız mevcut orchestrator `.mjs` CLI ve built-in testleri için gerekir; uygulama stack'i kararı değildir. CI, kaynak yapıda olduğu gibi Node 20 kullanır; harici npm paketi gerekmez.

## Ürün gereksiniminden değerlendirilecek alanlar

| Alan | İhtiyaç / karar girdisi |
|---|---|
| Ortak temel | Profil, takım, proje referansları, rol ve kaynak bazlı erişim; ürünler arası sahiplik |
| FIRST | Repo/proje keşfi, katkı geçmişi; GitHub bağlantısının kapsamı ve kapalı repo izinleri |
| STEP | İlan/teklif/anlaşma, saatlik/sabit bütçe, ödeme akışı; AI tahmin sınırları; takipte kullanıcı kontrolü ve saklama |
| INTO | Mentor uzmanlığı, müsaitlik, kabul/ret, görüşme ve ücretli/gönüllü ayrımı |
| PATH | Yarışma formatı belirlendikten sonra veri seti, çözüm teslimi, değerlendirme ve olası güvenli kod/model çalıştırma |

Seçim sırası: kullanıcı akışı ve MVP kapsamı → entegrasyon/veri/yetki sözleşmesi → framework/DB/sağlayıcı kararı → uygulama ve gerçek test araçları. Ortak sistemin tek uygulama mı ayrı uygulamalar mı olacağı henüz kararlaştırılmadı; orchestrator'ın ortak olması bunu belirlemez.

Bir teknoloji kararı gerektiğinde mevcut kod ve ekip kısıtlarını incele; dış API/ürün sürümüne ilişkin kararları güncel resmi belgelerle doğrula. Kararı run `decisions` içinde gerekçesiyle kaydet. Sadece orkestrasyon kurmak için ürün framework'ü kurma veya sağlayıcı hesabı açma.
