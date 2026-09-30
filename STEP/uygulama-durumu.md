# STEP — Uygulama durumu ve kapsam izi

30 Eylül 2026. Kabul edilen 52 karar temelinde backend, web ve Windows/macOS/Linux takip istemcisi kaynakları geliştirildi. Kaynak/diff incelemesi ile çalışma zamanı ve canlı sağlayıcı doğrulaması ayrı tutulur. İlk canlı ürün hazır veya yayımlanmış olarak raporlanmaz.

| Modül | Gerçek backend kaynakları | Web / masaüstü karşılığı | Kabul izi |
|---|---|---|---|
| M01 Hesap ve doğrulama | `core/accounts.py`, `security.py`, `common.py` | auth, account, verify/reset ekranları; desktop device login | AK-01.1–5; testte e-posta/şifre, canlı uygunluk kapıları |
| M02 Profil ve keşif | `accounts.py`, `api.py`, `serialization.py` | people, account, jobs; manuel FIRST proje/katkı portföy linkleri | AK-02.1–4; genel bilgiler ve özel dosyalar ayrı |
| M03 İlan/teklif/davet | `market.py`, `models.py` | market, employer, applications | AK-03.1–5; çoklu ayrı sözleşme, davette ücretsiz teklif |
| M04 Sözleşme ve değişiklik | `contracts.py`, `payments.py` | contracts ekranları; tüm maddi şartların karşılıklı kabulü | AK-04.1–4; iptal/itiraz hedefli, ödeme yarışı engelli |
| M05 Takım ve lider | `market.py`, `contracts.py` | teams, çalışan/ücret seçimi ve lider onayları | AK-05.1–6; takım kredi hesabı ve tek ödeme alıcısı |
| M06 Kredi ekonomisi | `common.py`, `market.py`, `payments.py`, `operations.py` | credits, boost, admin policy/grant/refund | AK-06.1–6; süresiz kredi, miktarlar ayarlanabilir |
| M07 TRY para/fon/çekim | `payments.py`, `providers.py`, ledger modelleri | money, fonlama ve admin uzlaştırma kuyrukları | AK-07.1–6; %10 freelancer, test/gerçek sağlayıcı ayrı |
| M08 Saatlik çalışma | `contracts.py`, `tracking.py`, `operations.py` | hafta, manuel süre/onay, iş günlüğü; native tracker | AK-08.1–5; ortak takım limiti, rate snapshot, 5 günlük inceleme |
| M09 Sabit iş ve teslim | `contracts.py`, `payments.py` | aşama/fonlama/teslim/dosya/revizyon | AK-09.1–4; ön fon, yeniden teslimde 14 gün yenileme |
| M10 Tracker ve gizlilik | `tracking.py`, `security.py`, `operations.py` | `desktop/step_tracker`; web worklog, privacy/case incelemesi | AK-10.1–8; seçili ekran, şifreli offline kuyruk, moderasyon öncesi hold |
| M11 İletişim/bildirim | `operations.py`, `common.py`, outbox | messages, notifications, preferences | AK-11.1–4; ilişki kapsamı ve özel dosya erişimi |
| M12 Destek ve yönetim | `operations.py`, `admin.py`, `management/commands` | admin categories/universities/policy/queue/audit, support | AK-12.1–5; ayrı görev izinleri, gerekçe ve case grant |

Kaynak dizinleri: [backend](backend/README.md), [web](frontend/README.md), [desktop](desktop/README.md). Ortak [API](contracts/api.md), [veri modeli](contracts/domain.md), [tracker](contracts/desktop.md), [sağlayıcı](contracts/providers.md) sözleşmeleri ve [teknik kararlar](teknik-kararlar.md) uygulamanın sınırlarını açıklar.

## İlk test için hazırlananlar

Docker Compose PostgreSQL/backend/worker/web servislerini ve private volume'u tanımlar. Gerçek yerel `.env` ve frontend `.env.local` hazırlandı; gizli değerler public Git deposuna gönderilmez. Yönetim komutu gerçek operatör hesabını gizli şifre girişiyle kurar ve altı başlangıç kategorisini oluşturur. Test modu yalnız e-posta/şifre kullanır; açık local simulator gerçek banka veya PSP sandbox sonucu sayılmaz.

Kredi ücretleri, ücretsiz hak miktarları, kredi satış fiyatı, öne çıkarma süresi, idle/preview ve çekim koşulları henüz seçilmiş ticari değerler değildir. Yönetim politikası yapılandırılmadan ilgili işlemler anlaşılır hata verir. Test kredisi yalnız yetkili operatörden dağıtılır. [Kurulum ve dağıtım](deployment.md) gereken komutları içerir.

## Canlıya geçişte tamamlanacak dış işler

- Gerçek SMTP ve Netgsm hesabı/anahtarları, üniversite öğrenci alan adı listesi ve işveren kimlik/kurum/yetkili kanıt süreci.
- iyzico işletme/KYC/underwriting kabulü ve sandbox/live anahtarları. Hosted checkout, alıcı kaydı, item approval ve refund kaynakları mevcut; sağlayıcıya canlı çağrı yapılmadı.
- Saatlik unused funds/rollover ve talebe bağlı banka çekiminin sağlayıcı tarafından desteklenen sözleşmesi/adaptörü. Mevcut kaynak, doğrulanmamış banka kabiliyetini `unavailable`/`missing_operation` ile kapatır; tahmini transfer alanı veya operatör paid bayrağıyla başarı üretmez. Bu alan yalnız anahtar eklemekle tamamlanmış sayılmaz.
- Windows/macOS/Linux hedeflerinde native paket üretimi, imza/notarization, güncelleme/dağıtım ve OS izinleri. Linux kaynak desteği X11 içindir; Wayland eksik sayaç/aktif uygulama kaydıyla ücretli takibe başlamaz.
- HTTPS hedefleri, ayrı canlı veritabanı, özel dosya yedekleri, onaylanmış politika ve operasyon sorumlulukları. Test ledger/verisi canlıya taşınmaz.

FIRST kaynakları ve veritabanı bu teslimde değiştirilmedi. Ortak giriş/otomatik FIRST aktarımı, AI ilan desteği, INTO inceleme bağlantısı ve PATH kapsamı sonraki ürün işleridir.

## Kontrol ve teslim sınırı

Bağımsız kaynak incelemelerinde bulunan açıkları düzeltmek için ayrı revizyonlar tutuldu; önceki başarısız sonuçlar silinmedi. Görev grafiği ve kanıtlar `.orchestrator/runs/step-full-development/` altındadır.

Kullanıcı tercihi gereği test yazma/çalıştırma, lint, typecheck, Docker/Next/native build, DB migration uygulama, tarayıcı/computer use, ekran kaydı/listener veya gerçek sağlayıcı/SMTP/OTP çağrısı yapılmadı. Initial migration yalnız uygulama kaynağı olarak üretildi. Bu nedenle kurulum, gerçek ödeme ve üç OS çalışma davranışı çalışma zamanında doğrulanmış değildir.
