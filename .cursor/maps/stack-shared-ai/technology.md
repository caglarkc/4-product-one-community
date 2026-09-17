# Teknoloji durumu ve entegrasyon ihtiyaçları

## Kesin durum

Repo henüz uygulama kodu içermiyor; FIRST için teknoloji seçildi: backend Python + Django + Django REST Framework, Hetzner üzerinde Docker; ayrı frontend TypeScript + React + Next.js, Vercel üzerinde. İlk hedef web sitesidir. Kaynak: `FIRST/teknik-kararlar.md`.

Giriş/kayıt Google, GitHub ve e-posta/şifre ile olacak. Repo başvurusu için doğrulanmış e-posta ve bağlı GitHub; ilan oluşturmak için ayrıca doğrulanmış telefon ve repo yetkisi gerekiyor. Kaynak: `FIRST/auth-kararlari.md`.

Veritabanı, auth kütüphanesi, oturum modeli, e-posta ve telefon doğrulama sağlayıcıları seçilmedi. Öğrenci doğrulama hizmetleri araştırıldı, satın alma/entegrasyon kararı yok: `FIRST/ogrenci-dogrulama-arastirmasi.md`. Orchestrator'ın Node CLI/CI sürümü ürün runtime sürümü kararı değildir.

## Ürün gereksiniminden değerlendirilecek alanlar

| Alan | İhtiyaç / karar girdisi |
|---|---|
| Ortak temel | Profil, takım, proje referansları, rol ve kaynak bazlı erişim; ürünler arası sahiplik |
| FIRST | Repo/proje keşfi, katkı geçmişi; GitHub bağlantısının kapsamı ve kapalı repo izinleri |
| STEP | İlan/teklif/anlaşma, saatlik/sabit bütçe, ödeme akışı; AI tahmin sınırları; takipte kullanıcı kontrolü ve saklama |
| INTO | Mentor uzmanlığı, müsaitlik, kabul/ret, görüşme ve ücretli/gönüllü ayrımı |
| PATH | Yarışma formatı belirlendikten sonra veri seti, çözüm teslimi, değerlendirme ve olası güvenli kod/model çalıştırma |

Ürünler ayrı siteler olarak sunulacak, hesaplar ileride ortak olacak. Bunun ortak veritabanı, tek backend veya belirli bir SSO çözümü anlamına geldiği kararlaştırılmadı. API tasarımı kullanıcı akışları üzerinden sırayla ilerleyecek; önce auth. Seçilmiş framework'ler tüm API/veri/yetki sözleşmelerinin tamamlandığı anlamına gelmez.

Bir teknoloji kararı gerektiğinde mevcut kod ve ekip kısıtlarını incele; dış API/ürün sürümüne ilişkin kararları güncel resmi belgelerle doğrula. Kararı run `decisions` içinde gerekçesiyle kaydet. Sadece orkestrasyon kurmak için ürün framework'ü kurma veya sağlayıcı hesabı açma.
