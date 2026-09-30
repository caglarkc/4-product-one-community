# STEP Tracker — native desktop kaynakları

PySide6 Widgets uygulaması; Windows, macOS ve Linux **X11** için native ekran/etkinlik katmanları içerir. Bu teslim kaynak kodudur. Üç işletim sistemi paketi oluşturulmadı, imzalanmadı veya fiziksel cihazlarda doğrulanmadı. Wayland'de tam giriş/screen/app kabiliyeti varsayılmaz; uygulama X11/Xorg oturumu seçilmesini açıklayıp başlatmayı kapatır.

## Kaynak sınırı ve çalışma akışı

- `step_tracker/ui.py`: HTTPS backend ve e-posta/şifre cihaz girişi, kayıtlı cihazı açma, sözleşme/fon ve fiziksel ekran seçimi, çalışma açıklaması, başlat/duraklat/elle devam/durdur/senkronizasyon ve idle otomatik devam, kişisel PNG önizlemesi ve açık yayın/moderasyon eylemleri. Ağ ve kayıt işleri GUI iş parçacığında çalışmaz. Görüntü bellekte gösterilir; PNG temp dosyası veya public URL yoktur.
- `step_tracker/native.py`: MSS ile `monitors[1:]` fiziksel ekran listesi ve yalnız seçilen ekranın bölgesi. Giriş callback'leri yalnız sayaç ve son etkinlik zamanını günceller; keycode/tuş içeriği, fare koordinatı/button kimliği veya pencere başlığı saklamaz. Windows executable basename, macOS NSWorkspace uygulama kimliği/adı ve X11 WM_CLASS kullanılır; alan 160 karakterle sınırlıdır ve yol/satır sonu reddedilir. Kamera, video, ses veya OCR kaydı yoktur.
- `step_tracker/engine.py`: açık kullanıcı başlatması sonrası gerçek izin/probe kontrolü; sunucudan `requested_seconds=600` teknik yetki paketi. Monotonic süre ve gerçek `authorized_until`/`reserved_seconds-used_seconds` sınırının küçüğü uygulanır. Başlangıç/yanıt gecikmesi nedeniyle bölüm 600 saniyeden kısa olabilir. Ortak takım `remaining_seconds` göstergesi cihazın çevrimdışı bütçesi değildir.
- Her bölümde, yetki sonuna capture payı bırakan rastgele bir anda tek çalışma PNG'si alınır. Başlangıç kabiliyet probe'u da yalnız seçili ekrandan yapılır; probe byte'ları saklanmaz/gönderilmez. Kullanıcı erken durdurursa kısa bölüm henüz PNG içermeyebilir. Görüntü yakalama/izin kaybı, monitör değişimi, uygulama bilgisi hatası veya yerel işçi kesintisinde son doğrulanan noktada durur. Tam batch sınırına PNG olmadan gelen bölüm normal tamamlandı kabul edilmez.
- Sunucu `idle_seconds` politikasını göndermediyse takip başlamaz; istemci yeni ürün varsayılanı uydurmaz. Idle'da bölüm son etkinlik noktasında kapanır; eşik bekleme aralığı ücretli süreye eklenmez. Idle bekleyişinde yalnız içeriksiz input sayacı/son etkinlik zamanı tutulur; yeni capture, app sorgusu, ücretli süre veya draft üretilmez. Yeni native etkinlik otomatik devam niyetini oluşturur. Önce önceki bloklar, pending privacy ve server stop ACK'leri tamamlanır; ardından native capability probe ve çevrimiçi yeni funded grant ile devam edilir. Ortak/kalan/eski grant idle sonrasında yeniden bütçe sayılmaz. Kullanıcı duraklatma/durdurma, native/network/auth/politika hatası ve uygulama kapanışı idle bekleyişini/sayaçları kapatır; bu durumlar kendiliğinden devam etmez, elle Başlat/Devam gerekir. Aktif kayıt ağ kesintisinde **mevcut cihaza ayrılmış** yetkinin içinde sürer; yeni yetki çevrimiçi ve önceki upload/stop ACK'lerinden sonra alınır. Çökme sonrası şifreli checkpoint kurtarılıp senkronize edilir; ücretli kayıt kendiliğinden devam etmez.
- `step_tracker/storage.py`: token/queue key yalnız güvenli OS keyring backend'lerinde; AES-GCM 256-bit key, her yazımda OS random 12-byte nonce ve record-kind/UUID AAD. SQLite/WAL yalnız şifreli payload içerir; parola SQLite'a yazılmaz. Güvenli keyring, doğru AES key veya doğrulanan ciphertext yoksa kayıt başlamaz; plaintext fallback yoktur. Tam blok, grant final-ID listesi ve draft silinmesi yerel tek transaction ile promote edilir.
- `step_tracker/api.py` / `sync.py`: doğrulanan TLS, scoped Bearer, timeout, redirect kapalı; uzak HTTP yok. Yalnız açık yerel geliştirme seçimi localhost/loopback HTTP'yi açar. Mutasyon UUID'leri, sıralı JSON ve deterministik multipart boundary/PNG byte'ları aynı retry gövdesini korur. 409/in-progress, timeout ve bilinmeyen sonuçta başlatma/blok kaydı korunur. 401 cihaz girişini yenilemeyi gerektirir. Ham credential, PNG veya request/error body loglanmaz.

## Görüntü gizliliği ve tekrar deneme

Yeni görüntü sunucuda `publication_ready_at=null` özel preview'dur. Upload tamamlandı diye review-ready veya publish otomatik gönderilmez. Öğrenci için silme düğmesi/endpoint'i yoktur.

İlk dispatch öncesi kişisel bilgi seçimi blok payload'ına atomik `privacy_intent`/gerekçe olarak girer. İlk dispatch başladığında payload/digest değişmez. Sonuç bilinmiyorsa aynı blok UUID/byte'ları yeniden gönderilir; sonra seçilen kişisel bilgi talebi ayrı **şifreli pending action** olur. Screenshot ID öğrenilince privacy POST doğrulanır; bu ACK tamamlanmadan blok/grant kapatması veya yeni yetki verilmiş sayılmaz. Bekleyen privacy varken yayın eylemi gönderilmez. Publish/review-ready dispatch'inin sonucu bilinmiyorsa aynı eylem uzlaştırılana kadar diğer kararlar kilitlidir.

Preview dialog'u açık güvenli yayın onayı ve explicit review-ready sağlar. Preview süresi, owner review-ready sunucu alımından başlar; istemci capture saatinden yayın zamanını hesaplamaz. Review-ready yanıtı kesinleşince henüz preview'da kalan görüntü için kişisel bilgi talebi yeniden seçilebilir; sunucu yayın yarışında nihai otoritedir. Talep süreyi/ücreti otomatik azaltmaz. Moderatör kararı web/backend kapsamındadır.

Sunucu ACK sonrası kesinleşmiş owner eyleminde yerel şifreli PNG kopyası dahili cache temizliğiyle bırakılır; gerektiğinde owner-authenticated image endpoint'inden belleğe alınır. Karar verilmemiş ACK'li yerel kopya en fazla 90 günlük cache sınırında temizlenir. Henüz ACK almamış/bilinmeyen outbox PNG'si yeniden gönderim kanıtıdır ve otomatik atılmaz. Sunucudaki 90 günlük saklama ve aktif itiraz hold'u backend'in yetkisindedir; yerel cache temizliği server kanıtını veya ledgerı silmez.

## Yerel kullanım — kullanıcı/operatörün çalıştıracağı komutlar

Python 3.13, hedef işletim sistemi ve masaüstü oturumu gerekir. Aşağıdaki komutlar bu görevde çalıştırılmadı:

```sh
cd STEP/desktop
python3.13 -m venv .venv
# macOS / Linux
.venv/bin/python -m pip install -e .
.venv/bin/python main.py
# Windows PowerShell
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe main.py
```

Backend adresi kullanıcı tarafından verilir. Test için backend'in email/password hesabı, kabul edilmiş aktif sözleşme, fonu ve idle politikası gerekir. Test girişi öğrenci/işveren canlı doğrulaması yapıldığı anlamına gelmez. İstemci ödeme, kredi veya rol doğrulaması gerçekleştirmez; server tracker izinlerine uyar. Görüntü listesi son doğrulanan server yanıtını gösterir; moderasyon/retention için web/backend nihai kaynaktır. Giriş token'ının süresi dolar/iptal edilir; aynı hesapla “Cihaz girişini yenile” kuyruk kimliklerini değiştirmeden auth'u yeniler.

## OS izinleri / dağıtım koşulları

| Hedef | Native API ve paket dışı koşul |
|---|---|
| Windows | MSS/Win32 capture, pynput hooks, GetForegroundWindow → PID → QueryFullProcessImageNameW basename. Secure keyring Windows Credential Manager. Kullanıcı masaüstü oturumu gerekir; UAC/secure desktop/protected process erişimi başarısızsa ücretli kayıt durur. Kurumsal endpoint koruması ve Authenticode dağıtım imzası hedef ortamda değerlendirilir. |
| macOS | CGPreflightScreenCaptureAccess / CGRequestScreenCaptureAccess, CGPreflightListenEventAccess / CGRequestListenEventAccess, AXIsProcessTrustedWithOptions. Ekran Kaydı, Giriş İzleme ve Erişilebilirlik izinleri kullanıcının Sistem Ayarları → Gizlilik ve Güvenlik ekranındadır; izin düğmesi istek yapar, kabul varsaymaz. NSWorkspace native app kimliği; Keychain queue key/token. Signed app kimliği değişirse TCC izinleri tekrar gerekebilir. |
| Linux X11 | Açık Xorg/X11 DISPLAY, MSS X11 capture, pynput XRecord, python-xlib `_NET_ACTIVE_WINDOW`/WM_CLASS. Masaüstü/WM bu kabiliyetleri vermelidir. Secret Service (SecretStorage) veya desteklenen güvenli KWallet keyring açık olmalıdır; keyring kilitli/missing ise kayıt başlamaz. X11/XRecord veya WM_CLASS eksikliğinde başarı taklidi yoktur. Wayland/XWayland sınırlı event desteği tam takip sayılmaz. |

OS izinleri ancak gerçek paket ve kullanıcı oturumunda doğrulanabilir. Bu kaynak teslimi Windows/macOS/Linux desteğinin dağıtımda tamamlandığını kanıtlamaz.

## Native paketleme — çalıştırılmamış kaynak yolu

`pysidedeploy.spec` Widgets/QML'siz standalone Nuitka/PySide6 manifestidir. `build.py` mevcut hedef OS için Python yolu, source/output yolları ve native dynamic paketleri ekleyen ignored `deployment/` spec üretir; tracker modülünü/capture/listener'ı import etmez. Kaynak manifest ve `.gitignore` build/env/database/imza anahtarlarını repo tesliminden ayırır.

```sh
# macOS / Linux native host; Qt deployment tool pip PySide6 ile gelir
.venv/bin/python build.py --dry-run
.venv/bin/python build.py
# Windows native host
.venv\Scripts\python.exe build.py --dry-run
.venv\Scripts\python.exe build.py
```

Her hedef kendi native host'unda ayrı derlenir; C/C++ toolchain, Nuitka dependencies ve Qt platform plugin'leri paket ortamında tamamlanır. Windows `.exe` ve yanındaki standalone runtime; macOS `.app`; Linux `.bin` ve runtime/Qt-xcb bağımlılıkları `dist/` altında oluşturulur. PySide6/Nuitka versionlarına göre tam artifact adı native packaging çıktısından teyit edilir; bu görevde artifact yoktur.

macOS'ta PyObjC/AppKit/Quartz/ApplicationServices/objc ve Windows/Linux'ta ilgili dynamic input/keyring backend'leri dahil edilir. Hardened runtime, tüm gömülü native bileşenlerin Developer ID imzaları, `codesign` doğrulaması, Apple `notarytool` gönderimi ve stapling ayrı release adımıdır. Geçerli Apple Developer team/cert/keychain profile ve Windows dağıtım sertifikası dış girdidir; repo bunları üretmez, içermez veya başarıyla imzalandığını iddia etmez. macOS izinleri dağıtılacak bundle üzerinden, Linux Qt-xcb/X11 ve secure keyring hedef dağıtımlar üzerinden, Windows hook/monitor/credential davranışı gerçek cihazda ayrıca değerlendirilmelidir.

## Kaynak incelemesiyle kabul eşleştirmesi

- Gerçek OS, selected-monitor ve içeriksiz input/app: `native.py`; GUI'de tek ekran seçimi `ui.py`.
- Fon/limit, teknik600, monotonic/idle otomatik devam ve offline sınırı: `engine.py`; server reserved-grant/UUID DTO doğrulaması `sync.py`.
- Şifreli outbox, atomik checkpoint ve unknown retry: `storage.py`, `api.py`, `sync.py`.
- Owner preview, ilk-dispatch hold, pending privacy, explicit release/review ve ACK sonrası stop: `ui.py`, `engine.py`, `sync.py`.
- Üç native paket kaynağı ve izin/distribution dış koşulları: `requirements.txt`, `pyproject.toml`, `pysidedeploy.spec`, `build.py`, bu belge.

Kontrol yöntemi yalnız kaynak/diff okumasıdır. Test, lint/typecheck, build/smoke, uygulama çalıştırma, keyboard listener/screenshot çağrısı veya browser/computer use yapılmadı.
