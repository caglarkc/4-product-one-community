# STEP web

Bağımsız Next.js 16.3.5 / React 19.3.0 / TypeScript 6.0.3 istemcisi. Node 22 LTS gerekir. FIRST kaynağı, paleti, hesabı veya veritabanı kullanılmaz. API tek kaynağı `STEP/contracts/api.md` dosyasıdır.

`NEXT_PUBLIC_STEP_API_URL` yalnız browser-visible backend API adresidir. Yerel `.env.local` mevcut backend için `http://localhost:8002/api/v1/` içerir ve Git dışında tutulur; örnek `.env.example` dosyasındadır. Sağlayıcı/SMTP/kimlik anahtarı burada tutulmaz. Browser frontend ve backend aynı `localhost` host'unu kullanmalı; Django frontend origin/credentials CORS, CSRF_TRUSTED_ORIGINS ve session cookie ayarlarını sağlamalı. Uzak ortam HTTPS gerektirir. Cookie HttpOnly; client token/localStorage ile giriş saklamaz.

Kurulum için Node 22 ile `npm install`; geliştirme `npm run dev` (3001), üretim `npm run build` ve `npm run start`. Dockerfile standalone çıktı hazırlar; API URL build arg `NEXT_PUBLIC_STEP_API_URL` üzerinden sağlanır. Bu geliştirme turunda install, build, test, lint, typecheck veya tarayıcı çalıştırılmamıştır; sürüm çözümü, gerçek render, ödeme/SMTP ve erişim davranışı runtime'da doğrulanmış değildir.

## Ekranlar ve kapsam

- M01: kayıt/giriş/sıfırlama, `/account` öğrenci/telefon/işveren/ödeme alıcısı başvuruları; ilk testte ek kapıların ertelendiği açıklanır, verified durumu yalnız server cevabından gelir.
- M02–M03: `/jobs`, `/jobs/[id]`, `/people`, `/people/[id]`, `/employer`, `/applications`: filtreli/sayfalı keşif, özel dosyalar, yayın/davet/başvuru, teklif değişikliği/geri çekme ve her başvuru için ayrı sözleşme.
- M04–M05: `/contracts/new`, `/contracts/[id]`, `/teams`, `/teams/[id]`: karşılıklı koşul kabulü/değişiklik, çalışan ücret snapshot'ları, lider ve açık ödeme alıcısı onayları, ayrı takım kredi hesabı.
- M06–M07: `/credits`, `/money`: server fiyatı, nullable politika açıklaması, süresiz kredi, satın alma/iade isteği, hosted ödeme/reconcile, yalnız açık local simulator denemesi, kazanç/rezervasyon/banka transferi ayrı durumlar.
- M08–M10: sözleşme alanında haftalık fon ve ortak limit, manuel süre/onay, aşama fon/start/teslim/revizyon, 5/14 günlük inceleme, çalışma günlüğü. Authenticated blob görüntüsü; owner-safe-confirm publish/review-ready ve moderasyon talebi; silme yok. Masaüstü takibinin kendisi ayrı STEP desktop paketidir.
- M11–M12: `/messages`, `/notifications`, `/support` ve `/admin/**`: scoped dosya paylaşımı, tercihler, değerlendirme, hedefli destek, kredi/takip politikaları, üniversite alan adı/kategori, test grant, şikâyet/kimlik/itiraz/görüntü/çekim/iade/lider kuyruğu, audit. Personel görüntü incelemesi önce geçici case grant ister.

İşlem istekleri credentials+CSRF ve actor-scoped Idempotency-Key ile gönderilir. Aynı formun belirsiz/işleniyor sonucunda aynı intent anahtarı korunur; kesin 4xx politika/doğrulama reddinden sonra yeni deneme yeni anahtar alır. Değişen payload yeni intent'tir. Başarıyla gönderilen mesajın dosya seçimi temizlenir. Sağlayıcı checkout init başarı cevabı fonlanmış sayılmaz. Gerçek sağlayıcı hazır değilse işlem disabled/hata; mock sonuç veya sahte metrik yoktur. ListPage sonuç/count/next ve doğrudan object cevapları ayrı tüketilir.

Eksik canlı dış ayarlar: backend host/origin/HTTPS, gönderici SMTP, üniversite domain listesi, nullable tutarlar, provider şirket/KYC/iş modeli/ürün yetkileri ve bank payout kabiliyetleri. Bunlar frontend başarılı sonuçla aşılmaz. FIRST otomatik veri, INTO/AI, SSO ve sonraki ürün özellikleri bu kaynakta sunulmaz.

Kategori bağlantı adı backend tarafından isimden türetilir; kategori formu kullanıcıdan yok sayılan slug alanı istemez. Politika ekranı çekim takvimini boş/belirlenmiş olarak yönetir; banka hazır durumu ayrıca server capability alanıdır. Üniversite/kategori PATCH güncelleme ve görüntü inceleme erişimlerinin backend sözleşmesine bağlı olduğu kaynak incelemesinde takip edilmiştir.

## Kaynak revizyonu

Koşul değişikliği kabul kartı kapsam, revizyon, süre, takip, sözleşme ücreti/ortak limit, öğrenci başına ücret ve mevcut/yeni aşama tutarlarını mevcut → önerilen biçiminde gösterir. İsimler server profil/üye verisinden çözülür; eksik veya hatalı maddi veri ve tamamlanmamış seçim yüklemesi kabulü kapatır. Takım hesabı/başvuru seçimi bütün ListPage sayfalarını alır; kendi teklif/davet eylemleri bireysel actor veya güncel liderle sınırlandırılır.

Staff itiraz incelemesi açık case grant sonrasında yalnız hedef haftayı/aşamayı, teslim dosyalarını, manuel süre kararlarını, takip kayıtlarını ve server hesap esasını gösterir; grant/veri olmadan release/refund kararı kapalıdır. Sabit hedef tutarı/saatlik hesap tutarı banka transferi kanıtı değildir. Grant süresi bittiğinde kanıt görünümü kapanır.

Yerel ödeme alıcısı kaydı yalnız legal_name/iban ister; simulated/provider_verified=false gerçek sağlayıcı kaydı olarak sunulmaz. Simulator çekim sonucu yerel deneme olarak görünür; gerçek paid banka kanıtı gerekir. Failed + retry_allowed ödeme kontrollü yeni deneme açar, unknown yalnız uzlaştırılır. Yönetim ödeme/sağlayıcı işlemi uzlaştırma ve bekleyen manuel süre/çevrimdışı yetki kuyruklarını gösterir; başka actor adına süre veya kanıtsız paid oluşturmaz.

Pending takım sözleşmesinde server stale_team_leader verirse yalnız işveren mevcut şartları görünür yeni lider/alıcıyla yeniden teklif eder; eski kabuller sıfırlanır. Aktif lider değişikliği ayrı onay protokolüdür. Bu revizyonda da kontrol yalnız kaynak okumasıdır; install/build/test/lint/typecheck/browser çalıştırılmamıştır.
