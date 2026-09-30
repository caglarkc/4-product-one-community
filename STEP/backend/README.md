# STEP bağımsız backend

Python 3.13 / Django 5.2.17 / DRF 3.18.1 / PostgreSQL 18.6. FIRST modelleri, kimliği, veritabanı veya dosyaları kullanılmaz. API kaynak sözleşmesi `../contracts/api.md`, ürün davranışları `../urun-kapsami.md`.

## Kaynak yapısı

- `core/models.py`, `migrations/`: UUID kaynaklar, database constraints, ayrı kredi ve para kayıtları; immutable olaylar ve ortam damgası.
- `accounts.py`, `security.py`: web session + login dahil CSRF; üniversite e-postası, yıllık uygunluk, hash/nonce/HMAC telefon OTP; scoped/expiring/revocable device kimliği.
- `market.py`, `contracts.py`: kategori UUID, ilan/teklif/davet, takım/lider, karşılıklı versioned terms, aşama/revizyon/itiraz, hafta/saat limiti ve açık onaylı manuel süre.
- `payments.py`, `providers.py`: TRY Decimal, %10 freelancer payı, test/sandbox/live ayrımı, hosted initialize/retrieve/onboard, held item release/refund, bilinmeyen ağ sonuçları ve banka operasyon kanıtı.
- `tracking.py`: server-reserved 600 saniyelik teknik capture grants, ortak takım limiti, owner/client UUID+digest, overlap koruması, encrypted offline istemcinin batch ingest'i, atomik privacy intent ve review-ready.
- `operations.py`: private scoped dosyalar, mesaj/değerlendirme/bildirim, gerçek yönetim kuyrukları, case investigation grant, tick/outbox ve 90 günlük özel görüntü temizliği.
- `api.py`, `serialization.py`: tek route registry ve açık izin/DTO sınırları. DB-only mutasyonun idempotency kaydı, iş etkisi ve response'u aynı transaction'da; external IO ayrı kısa transaction/uzlaştırma sınırlarında.

## Ortam ve ilk kurulum

Docker compose ana integration writer'ın `../compose.yaml` dosyasında. Environment gerçek `../.env` üzerinden verilir; secrets image veya Git teslimine girmez. `backend/.dockerignore` private volume, venv, static ve env dosyalarını dışlar.

Gereken çevre alanları:

- `STEP_SECRET_KEY`, `STEP_FIELD_ENCRYPTION_KEY` (32 byte hex veya URL-safe base64), `STEP_DEBUG`, `STEP_MODE=test|live`, `STEP_PAYMENT_PROVIDER=simulator|iyzico_sandbox|iyzico_live`.
- `STEP_DB_NAME`, `STEP_DB_USER`, `STEP_DB_PASSWORD`, `STEP_DB_HOST`, `STEP_DB_PORT`, `STEP_PRIVATE_ROOT`.
- `STEP_ALLOWED_HOSTS`, `STEP_WEB_ORIGINS` (exact origins), `STEP_WEB_URL`, `STEP_API_URL`, isteğe bağlı `STEP_COOKIE_SAMESITE`. Cross-site `None` yalnız HTTPS/Secure; local development `Lax`.
- SMTP `STEP_SMTP_HOST/PORT/USER/PASSWORD/FROM/TLS`.
- `STEP_IYZICO_API_KEY`, `STEP_IYZICO_SECRET_KEY`, `STEP_SERVER_PUBLIC_IP`; `STEP_NETGSM_USER/PASSWORD/HEADER`.

Anahtar olmayan sandbox init/onboarding başarılı sayılmaz. Simulator yalnız açık DEBUG+test yerel fixture; üniversite/kimlik doğrulaması yapıldı veya banka para aktarımı doğrulandı iddiası değildir. Test modunda ek uygunluk kapıları ertelenir; required öğrenci profil alanları ertelenmez.

EnvironmentState ilk işlemde mode/provider damgası oluşturur. Aynı DB'de test→live veya simulator→sandbox değişimi fail-closed olur. Yeni bağımsız DB/volume ve canlı yapılandırma gerekir; test bakiye/kazanç/sözleşme kayıtları taşınmaz.

Aşağıdaki komutlar backend dizininden, gerçek STEP ortam değişkenleri süreç ortamına verilerek çalıştırılır. Kaynaklar dotenv dosyasını kendiliğinden yüklemez; compose env_file aktarımını yapar. DB/server/operatör komutları bu teslimde çalıştırılmadı:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py step_operator --email operator@example.org --name 'STEP Operatör'
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000
.venv/bin/python manage.py step_tick --loop
```

`step_operator` gerçek operatörü, kabul edilmiş altı kategoriyi ve boş politikayı oluşturur. Sahte kullanıcı, iş, üniversite alan adı veya ticari rakam üretmez. Password terminalde gizli okunur. Policy/university/provider capabilities yönetimden yapılandırılır; politika eksikken ilgili işlem anlaşılır hatayla kapalıdır. Django admin finans ledgerlarını değiştirme/silme/add için kapatır.

## Finans ve dış kabiliyetler

Banka çekimi, serbest bırakılmış kazançtan rezervasyon açar. `requested/processing/unavailable` rezervi korur; güvenli reddedilen/gönderilmemiş operasyon rezervi geri verir. Aynı kaynak payment bank sonucu `BankSettlement` unique kaydıyla ikinci kez ödenemez. Tam IBAN HMAC'le bağlanır; transient input/provider dışında yalnız şifreli çekim alanında saklanır, DTO maskelidir.

Gerçek iyzico Marketplace onayı ile Mass Payout aynı kazancı ikinci kez göndermez. On-demand withdrawal/partial release/rollover için sağlayıcı iş modeli ve işlem bazlı bank proof teyidi harici gereksinimdir. Destination-specific bank proof bulunmadan `paid` yazılmaz. Operasyon kuyruğu eksik provider operasyonunu, unknown/blocked durumunu ve ilgili hedefi görünür tutar. Resmî checkout/reporting belgeleri destination-bound completed bank sonucu tanımlamadığından gerçek PayoutGateway unavailable döner; checkout onayından banka ödendi sonucu çıkarmaz. Canlı on-demand sözleşmesi ve gerçek bank-result API kanıtı olmadan bu kaynakta gerçek çekim tamamlanamaz. Local simulator çekim sonucu operatörün açık success/failure fixture seçimiyle yürür; bank_transfer_proven false ve fixture kaynakları ayrıdır.

Haftalık kullanılmayan fon için Rollover ve kaynak/hafta allocation kayıtları vardır. Simulator ortak held fonu sonraki haftanın rezervine aktarır; yeni tahsilat yalnız kalan ihtiyacı kapsar. Gerçek provider-backed rollover allocation ayrıca capability kapısından geçer. Network-mutasyon unknown sonuçları otomatik kör tekrara girmez. Owner `payments/{id}/retry/` yalnız kesin başarısız/nonpaid denemeyi yeniden sorgulayıp eski şifreli token/deneme kanıtını PaymentAttempt'te koruyarak yeni conversation UUID oluşturur. Funded/unknown sonucu veya token üretimi belirsiz initialize tekrar açılamaz. Admin ödeme ve provider-operation reconcile ekranları gerçek server retrieve/reporting çağrılarıyla bağlı proof'u araştırır; operator paid bayrağı kabul etmez. Refund raporunun terminal status anlamı sağlayıcı kanıtı vermiyorsa işlem ve eşleşen iade bilgisi unknown kuyruğunda kalır. Kaynak ledgerı ile fiziksel sağlayıcı hareketi aynı şey sayılmaz.

## Gizlilik ve kaynak kontrolü

Private storage webde/static/media/signed URL ile yayımlanmaz. Dosya indirme, worklog, case image ve preview aynı kaynak yetkisine bağlıdır. Public ilan/profil özel metadata açmaz; ilan dosyaları owner/application/invitation/ilgili worker scope'undadır. Görüntüde takım liderliği başka üyenin sahibi olma izni değildir; support yalnız açık case assignment ve ilgili kanıta erişir.

Yeni screenshot publication_ready_at=null; auto preview süre capture zamanından başlamaz. Privacy intent upload transaction'ında held olur. Öğrenci delete yoktur; moderator withhold/publish sonucu süre/ücreti otomatik düşürmez. Ekran/etkinlik 90 gün, açık itirazın ilgili kanıtı korunur; süre/para ledgerı bununla temizlenmez.

Bu teslimde dependency ortamı ve kaynak migration generation uygulanmıştır. Database migration, API/server/smoke, test, lint/typecheck, browser veya canlı sağlayıcı senaryosu çalıştırılmamıştır. Kaynak migration üretimi sırasında bağımsız `db` host'una history bağlantısı kurulamadı; migration uygulanmış veya DB tutarlılığı doğrulanmış değildir.

## Modül kabul kaynağı

Bu tablo kaynak uygulamasını izler; çalışma zamanı kabul kanıtı değildir.

| Modül | Kaynak davranış |
|---|---|
| M01 | accounts.auth/verification; security.DeviceAuthentication; ayrı test/canlı uygunluk kapıları |
| M02 | accounts.profile_endpoint, api.user_profiles/public_teams, Category ve step_operator |
| M03 | market.jobs/applications/invitations; default mine listesi, owner incoming ilişkisi |
| M04 | contracts.contracts/change_accept; karşılıklı versioned terms, stale leader/reoffer ve eski snapshot history |
| M05 | market.teams/leader_approve; aktif çalışanlar, ortak limit, team wallet ve açık payee; lider/aktif sözleşme baseline ve Team kilidiyle eski onay 409 |
| M06 | common.credit_change, accounts.initial_grants, market.refund_job/boost, payments.credit_purchase |
| M07 | payments.payment_start/reconcile/retry_payment/release_target/payouts; mode+ledger+PSP proof ayrımı |
| M08 | contracts.weeks/week_totals/manual_time, tracking.session_start/ingest; fon/saat/manuel onay/5 gün |
| M09 | contracts.milestones/open_dispute; yeniden teslim 14 gün, funded history immutable |
| M10 | tracking.ingest/file_response/screenshot_action/privacy_resolve; atomic hold, owner review-ready, case scope |
| M11 | operations.messaging/attachments/deliver_mail, api.notifications/preferences; private dosya/outbox |
| M12 | operations.admin_endpoint/claim/refund_requests/process_payout, payments.admin_reconcile_payment/reconcile_operation; yetki, audit, kuyruklar |

Gerçek alt üye oluşturma intent'i de ProviderOperation'da dayanıklıdır; kimlik/banka/iletişim payload'ı yalnız alan anahtarıyla şifrelenir. Timeout sonrası yeniden onboarding gönderilmez; yetkili operator dış ID ile submerchant retrieve yapar ve kayıtlı alıcı/IBAN/currency kanıtını karşılaştırır. Raw TCKN DTO/audit/log'a girmez. Kaynakların dış sağlayıcı çağrıları gerçek hesap üzerinde çalıştırılmış değildir.

Bağımsız kaynak incelemesi düzeltmeleri: bireysel ücret revizyonu aktif ContractWorker ücretine aynı transaction içinde yansır; önceden açılmış Week.rate_snapshot değişmez. Lider değişim isteği baseline lider ve tam aktif sözleşme kümesini saklar; son onay güncel küme/üyelikle yeniden kontrol edilir. Team kilidi sözleşme aktivasyonu, iptali ve tamamlanmasında da önce alınır. Açık aşama itirazının atanmış, yetkili ve süresi geçmemiş incelemecisi yalnız o aşamanın submission attachment_ids dosyalarını indirebilir; genel staff dosya erişimi açılmaz. Payout.bank_transfer_proven yalnız iyzico_live paid kaydında tutar ve IBAN digest ile bağlı BankSettlement kanıtından türetilir; simulator ve sandbox false verir. Başlangıç migration kaynağı baseline_leader alanıyla birlikte güncellendi; migration uygulanmadı.
