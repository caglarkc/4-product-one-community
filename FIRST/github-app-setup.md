# FIRST — Seçilen repoları paylaşma bağlantısı

Mevcut GitHub OAuth uygulaması yalnız giriş/hesap bağlama için `user:email` ister. Repo paylaşımı ayrı GitHub App kullanıcı yetkilendirmesini kullanır. Kullanıcı GitHub kurulum ekranında **Only select repositories** ile tek repo veya istediği repoları seçebilir.

## GitHub App ayarları

- Ad: FIRST Community Repositories
- Homepage: `https://first.alicaglarkocer.com`
- Redirect URI: `https://first.alicaglarkocer.com/github-repo/callback` (wildcard kapalı)
- Setup URL: `https://first.alicaglarkocer.com/projelerim/yeni?github_setup=1`
- Redirect on update açık, Expire user authorization tokens açık.
- Request user authorization during installation kapalı; FIRST kendi session/state/PKCE akışını başlatır.
- Device flow ve webhook kapalı. Bu aşamada yetki her repo işlemi ve ziyaretçi önizlemesinde GitHub API üzerinden tekrar kontrol edilir.
- Repository permissions: **Contents read-only**, zorunlu **Metadata read-only**. Organization/account/enterprise izni yok.
- Any account: başka kullanıcılar da kendi seçtikleri repolara kurabilir. Marketplace yayını yapılmaz.

İlk kurulum formunda Administration yazma izni otomatik güvenlik incelemesince reddedildi: repo silme/ayar değiştirme kapsamı mevcut paylaşım akışından geniş. Bu faz yalnız repo seçimi ve README okuduğu için yazma izinleri kaldırıldı. İleride issue/PR/davet işlevleri eklenirken gereken izinler ayrı ve açık olarak genişletilebilir.

## Backend yapılandırması

`FIRST/backend/.env.example` içindeki `GITHUB_APP_*` alanlarını kullan. `GITHUB_APP_CLIENT_ID` ve `GITHUB_APP_CLIENT_SECRET`, giriş OAuth uygulamasının anahtarları değildir. App ID ve slug da yeni App'e aittir.

`GITHUB_APP_TOKEN_KEY` kalıcı, bağımsız bir Fernet anahtarıdır. Kullanıcı access/refresh tokenları veritabanında bu anahtarla şifrelenir. Anahtarı plansız değiştirmek mevcut bağlantıların yeniden yetkilendirilmesini gerektirir. Bu faz App kullanıcı tokenı kullandığı için GitHub App private key gerekmez. İstemciye sağlayıcı tokenı veya secret gönderilmez.

`send-machine`, `projects/` runtime kaynaklarını ve allowlist içindeki App ayarlarını uzak backend'e taşır. Alıcı `deploy/configure.py` aynı anahtarları kabul eder. Ayarlar tamamlanmadan bağlantı başarıyla kurulmuş gibi gösterilmez.

## Güvenlik ve ürün sınırı

Callback state mevcut FIRST kullanıcısı, oturumu, güvenlik sürümü ve bağlı GitHub kimliğine bağlanır. App yetkilendirmesinde dönen `/user` kimliği bağlı GitHub hesabıyla aynı olmalıdır. `installation_id` query parametresi sahiplik kanıtı değildir. GitHub'dan uygulamanın installation bilgisi, seçili repo ve kullanıcının `permissions.admin` alanı doğrulanır.

E-posta doğrulaması zorunlu, telefon alanı ve telefon doğrulaması bu fazda koşul değildir. Bir repo için tek aktif paylaşım bulunur. Başlık ve kategori gereklidir; açıklama isteğe bağlıdır. README en fazla üç cümle/600 karakter düz metin olarak önizlenir. Kullanıcı önizlemeyi görerek paylaşır. Private reponun URL'si, repo kimliği ve dosyaları ziyaretçi yanıtına eklenmez. Public repo için GitHub bağlantısı gösterilir. Repo erişimi veya görünürlüğü doğrulanamazsa dış bağlantı ve README ziyaretçiye açılmaz.

Başvuru, davet, dosya gezgini ve private repodan seçilen dosyaları yayımlama sonraki fazdadır.

Kaynaklar: [GitHub App kullanıcı yetkilendirmesi](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app), [installation API](https://docs.github.com/en/rest/apps/installations#list-repositories-accessible-to-the-user-access-token), [Setup URL doğrulaması](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/about-the-setup-url).
