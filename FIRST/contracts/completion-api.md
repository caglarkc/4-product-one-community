# FIRST tamamlama API — 30 Eylül 2026

Temel adres mevcut doğrudan backend: `/api/auth/`. JSON, mevcut opaque Bearer
oturumu ve oturuma bağlı CSRF korunur. Public GET çağrıları anonim çalışabilir;
korumalı okuma/yazma anonim olarak tekrar denenmez. Yeni uygulamalar:
`profiles`, `messaging`, `moderation`. Aşağıdaki davranışlar kaynak sözleşmesidir;
canlı kabul kanıtları run teslim kaydında ayrı tutulur.

## Profil uzantısı — `community/extension/`

- `GET student/`: yalnız sahibine `{student:{verified,verified_at,expires_at,email}}`.
- `POST student/request/ {email}`: geçerli `.edu.tr` adrese 24 saatlik tek kullanımlık
  onay bağlantısı. Hesap e-postası doğrulanmış olmalı; kullanıcı/IP/adres hız sınırları
  uygulanır. Son isteğin nonce'u ve hesap security_version değeri bağlanır.
- `POST student/verify/ {key}`: yeni kimlik yaratmadan okul e-postasına erişimi
  onaylar. Takvimde 12 ay geçerli; aktif öğrencilik belgesi kontrolü değildir.
  Public yanıt okul e-postası içermez. `people/?student=true` yalnız süresi geçerli
  onaylı kişileri getirir; kişi keşfinde bu kişiler önce sıralanır.
- `GET/PATCH settings/ {share_private_stats:boolean}`: private toplam paylaşımı
  varsayılan kapalıdır; public tercih yalnız toplamları açar.
- `GET stats/`, `POST stats/refresh/ {}`: `{stats:{since,updated_at,public,private,
  share_private_stats,partial,scope}}`. Toplam alanları `merged_prs`, `commits`,
  `projects`, `roles:{owner,teammate,contributor}`. Veri elle güncellenir; başlangıç
  account.date_joined. GitHub araması default branch/erişilebilir repo/index
  kapsamındadır; ilk 100 sonuçtan proje sayısı türetildiğinde kısmi kapsam belirtilir.
  Private repo adı/içeriği saklanmaz veya dışarı verilmez.
- `GET people/<username>/`: `{student,stats,portfolio,certificates}` public
  allow-list. Profile gizleme/askıya alma ve bağlı GitHub UID geçerliliği uygulanır.
- `GET portfolio/`, `POST portfolio/ {repository:"sahip/repo"}`: public repo
  sahibi, kabul edilmiş FIRST katkıcısı veya doğrulanmış merged GitHub PR katkıcısı
  ekleyebilir. En fazla 20 repo kaynak sınırı. Repo metadata onaylı elle alınmış
  snapshot'tır. `DELETE portfolio/<uuid>/` yalnız sahibine açıktır.
- `GET certificates/`, `POST certificates/ {title,filename,content_base64}`:
  PDF/JPG/JPEG; PNG kabul edilmez. En fazla 10 belge, dosya başına 2 MiB,
  toplam özgün dosya boyutu 20 MiB. Uzantı ve magic birlikte kontrol edilir;
  credential-free izole raster dönüştürücü kullanılır. Ham dosya tutulmaz/indirilmez.
  `GET certificates/<uuid>/preview/` yalnız güvenli raster görüntüsü verir;
  `DELETE certificates/<uuid>/` yalnız sahibine açıktır. `self_declared:true`.

## Doğrudan mesaj — `messages/`

- `GET messages/?page=N`: `{conversations,count,next_page,previous_page}` (12 adet).
- `POST messages/ {username}`: `{conversation}`; 201 yeni / 200 mevcut konuşma.
  İki hesap arasında tek konuşma; kendine gönderim yok, doğrulanmış gönderici gerekir.
- `GET messages/<uuid>/?before=<id>`: `{conversation,messages,next_before}`;
  son 30 mesaj artan ID sırasında döner. Yalnız iki katılımcı erişebilir.
- `POST messages/<uuid>/ {body}`: 1–5000 karakter, `{message,conversation}`.
- `POST messages/<uuid>/read/ {through_message_id:string|null}`: yalnız gerçekten
  getirilen/görüntülenen mesaj ID'sine kadar monoton okundu kaydı; null boş konuşmada
  ilerletmez. ID aynı konuşmaya ait olmalı. `{unread_count}` yeni görülmeyen mesajları
  korur. Ek/dosya veya grup sohbeti yoktur.

## Tek yönetici — `administration/`

`me.user.is_administrator` yalnız `is_superuser`, doğrulanmış ve askıda olmayan
hesapta true olur. Client alanı yetki vermez. Mevcut yönetici
`first_administrator --user-id N --exclusive` komutuyla atanır; kişisel veri run'a
kopyalanmaz. API, diğer hesaplara 403 verir.

- `GET administration/`: rapor, gizlenmiş içerik ve askıda hesap toplamları.
- `GET reports/?status=&page=`; `PATCH reports/<uuid>/ {status,note}`:
  `received/in_review/resolved/dismissed`, `{report}`.
- `GET users/?q=&page=`; `PATCH users/<id>/ {action,reason}`:
  `hide_profile/unhide_profile/suspend/reactivate`, `{user}`. Bu hedef kullanıcının
  yanıtı mevcut browser oturum kimliğini değiştirmez.
- `GET projects/?q=&page=`; `PATCH projects/<uuid>/ {action,reason}`:
  `hide/unhide`, `{project}`. Gizleme feed, detay, task ve ekip proje listesinde
  uygulanır; arşiv/visibility ayarları ayrı korunur.
- `GET audit/?page=`: actor/action/target/reason/tarih; API üzerinden değiştirilemez.

Askıya alma tüm oturumları iptal eder; tekrar açma eski oturumları canlandırmaz.
Yönetici özel GitHub repo veya selected viewer erişimi kazanmaz. Şikâyet otomatik
yaptırım doğurmaz. Moderatör rolleri bu teslimde eklenmez.

## Mevcut sorun düzeltmeleri

Aramada `Replace`/`Lower` çıktısı `TextField` olarak açıkça tanımlanır. Public
config/filtre okumaları eski Bearer oturumundan bağımsızdır. Vitrin validation
ayrıntıları arayüzde gösterilir. Django ve yalnız FIRST nginx API body sınırı 4 MiB
JSON/base64 belge yüklemesini karşılar; decoded belge kotaları ayrıca uygulanır.
