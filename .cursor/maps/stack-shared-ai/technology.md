# Teknoloji durumu ve entegrasyon ihtiyaçları

## Kesin durum

FIRST uygulaması backend/frontend dizinlerinde mevcuttur: backend Python + Django + Django REST Framework, Hetzner üzerinde Docker; ayrı frontend TypeScript + React + Next.js, Vercel üzerinde. İlk hedef web sitesidir. Kaynak: `FIRST/teknik-kararlar.md`.

Giriş/kayıt Google, GitHub ve e-posta/şifre ile uygulanmıştır. Repo başvurusu için doğrulanmış e-posta ve bağlı GitHub; ilan oluşturmak için ayrıca repo yönetici yetkisi gerekir. Telefon doğrulaması şu an şart değildir. Kaynak: `FIRST/auth-kararlari.md`.

PostgreSQL, Redis oturum/güvenlik verisi, django-allauth, SMTP ve doğrudan HTTPS IP API kullanılır. Oturum Bearer ile taşınır; Next.js proxy yoktur. Telefon doğrulaması kapalıdır. Öğrenci doğrulama hizmetleri araştırıldı, satın alma/entegrasyon kararı yok: `FIRST/ogrenci-dogrulama-arastirmasi.md`. Orchestrator'ın Node CLI/CI sürümü ürün runtime sürümü kararı değildir.

## Ürün gereksiniminden değerlendirilecek alanlar

| Alan | İhtiyaç / karar girdisi |
|---|---|
| Ortak temel | Profil, takım, proje referansları, rol ve kaynak bazlı erişim; ürünler arası sahiplik |
| FIRST | Repo/proje keşfi, katkı geçmişi; GitHub bağlantısının kapsamı ve kapalı repo izinleri |
| STEP | E-posta/şifre testi, deneme ödeme/test kredileri; canlı hazırlıkta üniversite e-postası ve birey/kurum işveren kontrolleri. Süresiz kredi ile ayrı TL iş bedeli; %10 freelancer komisyonu; aşama/haftalık ön fonlama ve 14/5 günlük inceleme. Windows/macOS/Linux takip veri türleri, 10 dakikalık rastgele görüntü, 90 gün saklama ve yayın öncesi kişisel bilgi moderasyonu kabul edildi. Stack, sağlayıcı, API/veri/rol sözleşmeleri ve kalan sayısal parametreler teknik keşifte. Kaynak: `STEP/kararlar.md`, `STEP/gelistirme-plani.md` |
| INTO | Mentor uzmanlığı, müsaitlik, kabul/ret, görüşme ve ücretli/gönüllü ayrımı |
| PATH | Yarışma formatı belirlendikten sonra veri seti, çözüm teslimi, değerlendirme ve olası güvenli kod/model çalıştırma |

Ürünler ayrı siteler olarak sunulacak, hesaplar ileride ortak olacak. Bunun ortak veritabanı, tek backend veya belirli bir SSO çözümü anlamına geldiği kararlaştırılmadı. API tasarımı kullanıcı akışları üzerinden sırayla ilerleyecek; önce auth. Seçilmiş framework'ler tüm API/veri/yetki sözleşmelerinin tamamlandığı anlamına gelmez.

Bir teknoloji kararı gerektiğinde mevcut kod ve ekip kısıtlarını incele; dış API/ürün sürümüne ilişkin kararları güncel resmi belgelerle doğrula. Kararı run `decisions` içinde gerekçesiyle kaydet. Sadece orkestrasyon kurmak için ürün framework'ü kurma veya sağlayıcı hesabı açma.
