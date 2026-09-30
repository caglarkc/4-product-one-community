# STEP — Uygulama teknik kararları

30 Eylül 2026; tam geliştirme yetkisi kapsamındaki P0 seçimleridir. 52 ürün kararını değiştirmez. FIRST kaynakları/veritabanı ve dağıtımı bağımsız kalır.

| Katman | Seçim ve gerekçe |
|---|---|
| Backend | Python 3.13, Django 5.2.17 LTS, DRF 3.18.1; ilişkisel işlem/kilit ve hazır yönetim altyapısı. Bağımsız PostgreSQL 18.6. |
| Web | Next.js 16.3.5, React 19.3.0, TypeScript 6.0.3, Node 22 LTS; ayrı responsive web, gerçek API tüketimi, sade işlev odaklı yerleşim. |
| Desktop | Python/PySide6 Widgets; mss selectedmonitor, pynput sadece sayaç, OS activeapp adaptörleri; SQLite şifreli offline queue + AES-GCM/OS keyring. |
| İşlem | Decimal TRY ve integer kredi ayrı ledger; atomic/kilit, aktör+işlem scoped idempotency/request digest, provider outbox/reconciliation. |
| Oturum | Web HttpOnly session/CSRF + allowlisted credentials CORS; desktop hashed/revocable/expiring ve tracker-scope device token. |
| Özel medya | Private storage + auth endpoint; public/signed/static URL yok; dosya erişimi kaynak tarafı ve moderation status ile kontrol edilir. |
| Zamanlı iş | `manage.py step_tick` loop veya scheduler; DB lease/outbox, yeniden koşul kontrolü ve tekil olay anahtarı. |
| Ödeme | iyzico Marketplace adapter; sandbox ve live ayrı. Anahtar olmadan hosted ödeme başarı sayılmaz. `simulator` yalnız açık local development fixture. |
| Yayın | STEP'e ait Docker/compose, backend/web/private volumes. FIRST sunucusuna otomatik deploy yok; STEP host/domain/SMTP/provider alanları gerçek env ile yapılandırılır. |

Resmî kanıt: [Django](https://www.djangoproject.com/download/), [DRF](https://www.django-rest-framework.org/community/release-notes/#3181), [PostgreSQL](https://www.postgresql.org/support/versioning/), [Next](https://github.com/vercel/next.js/releases/tag/v16.3.5), [TypeScript](https://github.com/microsoft/TypeScript/releases/tag/v6.0.3), [Qt deployment](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html), [MSS](https://python-mss.readthedocs.io/latest/usage.html), [pynput limits](https://pynput.readthedocs.io/en/latest/limitations.html), [AES-GCM](https://cryptography.io/en/latest/hazmat/primitives/aead/).

## Ödeme sağlayıcı kabiliyetleri ve canlı kapıları

Hosted checkout init tek başına funded değildir. Server retrieve; merchant payment identity, hedef, TRY tutarı, payment status/fraud/transaction sonuçlarını doğrular. `conversationId` uygulama idempotency yerine geçmez. Network timeout sonrası kör ikinci tahsilat yerine pending reconciliation kullanılır.

Marketplace alt üye PERSONAL bireysel alıcıya uygundur; sağlayıcının TCKN/telefon/IBAN onboarding'i ödeme alıcısı KYC'dir, üniversite e-posta uygunluk yönteminin yerine geçmez. Platformun şirket/KYC ve iş modeli/kategori underwriting kabulü ayrıca gerekir. Kimlik alanları sohbet/run/audit çıktısına dökülmez; gerçek provider key ve kanıt yoksa live hazır değildir.

Approve/held hak ediş ve bank settlement ayrı durumlardır. İlgili transaction net freelancer payı %90, platform payı %10 olacak biçimde provider doğrulaması yapılır. Generic Mass Payout, Marketplace settlement ile aynı kazancı ikinci kez göndermek için kullanılmaz. Bank çekim isteği `paid` değildir; transfer sonucunun güvenilir reconciliation kanıtı gerekir. Partial release/unused weekly refund/rollover ve on-demand withdrawal kabiliyeti sözleşme teyidi yoksa live capability gate kapalıdır. Vergi/provider masrafından yeni ürün komisyonu çıkarılmaz.

Resmî araştırma: [iyzico Marketplace](https://docs.iyzico.com/), [iyzico platform başvurusu](https://www.iyzico.com/destek/yardim-merkezi/entegrasyon/hazir-altyapilar). Ayrıntılı provider kanıt raporu geliştirme run sonuçlarına kaydedilir.

## Parametreler ve doğrulama

Canlı fiyat/kredi miktarı, idle/preview, çekim alt limiti/takvimi ve özel sözleşme/payment retention rakamları seçilmiş sayılmaz. Politika alanları nullable ve yetkili yönetim tarafından yapılandırılabilir. Eksik zorunlu ayar ilgili işlemde anlaşılır hata, canlı readiness'te eksik gereksinim verir. İlk testte doğrulama kapıları ertelenir; kullanıcıya verified bayrağı yazılmaz. Test credits yalnız staff grant; başlangıç/aylık ücretsiz hak miktarları yapılandırılınca tekil grant işler.

Hafta teknik zaman hesabı Europe/Istanbul Pazartesi 00:00; 5 günlük employer review haftalık dönem kapanışında başlar. Farklı takım ücretinde ortak limit için en yüksek üye ücretinden güvenli reserve hesaplanır, gerçek kazanç her üyenin kabul edilmiş rate snapshot'ından hesaplanır; kullanılmayan fon refund/rollover seçimidir. Süreler UTC saklanır ve Türkiye zamanı gösterilir.

## Takip desteği ve gizlilik

Windows foreground executable basename, macOS NSWorkspace app adı/bundleid, Linux X11 WM_CLASS alınır; pencere/sekme başlığı ve tam dosya yolu alınmaz. macOS screen recording/input monitoring/accessibility ve seçili ekran erişimi doğrulanır. Wayland tam input/aktif app kaydı bu stack ile desteklenmez; açıkça X11 oturumu istenir, eksik kayıt ücretli takip olarak başlamaz. Üç OS paket kaynakları ayrı hedef ortamlarda build/sign edilir; build/izin/gerçek kayıt bu kaynak tesliminde doğrulanmış değildir.

Yeni screenshot private owner-preview'dır. Öğrenci kişisel bilgi olmadığını açık publish ile teyit edebilir veya privacy request açar. Configured preview interval varsa yalnız talep olmayan preview tick ile yayınlanır; interval yoksa otomatik yayın yoktur. Request ile publish aynı screenshot lock'ında yarışır. Moderator `withhold` (görüntü private saklanır) veya `publish` kararı verir; otomatik silme, maskeleme veya ücret/süre düşümü yoktur. Öğrenci silme endpoint'i yoktur. Ayrıntılı activity/görsel 90 gün, açık dispute kanıtı sonuçlanana dek saklanır; para ledgerı temizlenmez.

Bu seçimler kaynak uygulamasının başlangıcıdır; uygulama çalıştı, üç OS paketleri doğrulandı veya canlı para transferi yapıldı iddiası değildir.
