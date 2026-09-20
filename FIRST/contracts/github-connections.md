# FIRST — GitHub bağlantı envanteri

Kapsam: FIRST uygulama kaynaklarındaki GitHub HTTP çağrıları, tarayıcı yönlendirmeleri ve dış görseller. Aşağıdaki iç endpoint'lerin tabanı `/api/auth/` yoludur. GitHub giriş OAuth uygulaması ile seçili repolara erişen GitHub App ayrı yetkilerdir. FIRST oturum sorgusu ile GitHub token yenilemesi aynı işlem değildir.

## Backend HTTP çağrıları

| Tetikleyici | İç endpoint / kaynak | Dış GitHub endpoint'i | Ne zaman? |
|---|---|---|---|
| GitHub ile giriş, kayıt başlangıcı veya hesap bağlama dönüşü | `GET github/callback/` — `accounts/github_views.py: exchange` | `POST https://github.com/login/oauth/access_token`; `GET https://api.github.com/user`; `GET https://api.github.com/user/emails?per_page=100` | Kullanıcının GitHub giriş/bağlama aksiyonunun dönüşünde otomatik üç adım. Giriş token'ı repo işlemleri için saklanmaz. |
| GitHub App repo izninin dönüşü | `GET projects/github/callback/` — `projects/views.py: CallbackView` | `POST https://github.com/login/oauth/access_token`; `GET https://api.github.com/user` | İzin akışının dönüşünde kod değişimi ve bağlı hesap kimliği kontrolü. Repo erişim/yenileme token'ları şifrelenerek saklanır. |
| Repo listesinin ilk aktarımı veya kullanıcı yenilemesi | `GET / POST projects/github/repositories/` — `projects/snapshots.py: repositories`, `projects/github.py: authorized_repositories` | `GET https://api.github.com/user`; `GET https://api.github.com/user/installations`; kurulum başına `GET https://api.github.com/user/installations/{installation_id}/repositories` | GET yalnız daha önce başarılı aktarım yoksa GitHub'a gider; sonraki yenileme yalnız kullanıcının POST aksiyonuyla yapılır. Liste endpoint'leri sayfalanabilir. |
| “Paylaşımı hazırla” | `POST projects/github/preview/` — `projects/snapshots.py: prepare`, `projects/github.py: access_token, readme` | `GET https://api.github.com/repos/{owner}/{repo}/readme`; gerekiyorsa önce token yenilemesi | Kullanıcı repo seçip hazırlama düğmesine bastığında yalnız README alınır. Repo kimliği, kurulum, isim, açıklama ve görünürlük kayıtlı listeden gelir; repo listesi veya `/user` yeniden sorgulanmaz. README indirme adresi izlenmez. |
| Süresi bitmek üzere olan GitHub App erişim token'ı | `projects/github.py: access_token → token_request` | `POST https://github.com/login/oauth/access_token` (`grant_type=refresh_token`) | Token isteyen bir dış işlem sırasında, erişim token'ının kalan süresi 60 saniye veya daha azsa koşullu yenileme. Bağımsız zamanlayıcı değildir. |
| Repo iznini kaldırma, GitHub bağlantısını kaldırma veya FIRST hesabını silme | `POST projects/github/disconnect/`, `POST github/disconnect/`, `DELETE account/` — `accounts/reset_views.py`, `projects/github.py: revoke_authorization` | `DELETE https://api.github.com/applications/{github_app_client_id}/grant`; gerekiyorsa önce yukarıdaki token yenilemesi | Açık kullanıcı onayı ve yakın kimlik doğrulaması sonrası, saklı App kimlik bilgisi varsa. Paylaşılan GitHub App kurulumu veya repo silinmez. Uzak iptal başarısızsa yerel bağlantı kaldırılır ve kullanıcıya GitHub'da ek temizlik gerektiği bildirilir. |
| Eksik eski profil bilgisini tamamlama | Yönetici komutu `backfill_github_profiles` — `accounts/management/commands/backfill_github_profiles.py` | `GET https://api.github.com/user/{github_user_id}` | Yönetici komutu elle çalıştırılırsa; sayfa ziyaretine bağlı değildir. `--dry-run` da GitHub'dan okur, yalnız veritabanı yazımını atlar. |

Repo listesi çağrılarında yalnız ilgili GitHub App kurulumları ve kullanıcının yönetici olduğu repolar seçilir. Giriş, token, repo ve iptal isteklerinde otomatik HTTP redirect takibi kapalıdır. Parametreli yollar yalnız kimlik/kurulum/repo tanımlayıcılarıdır; bu belgede kullanıcı verisi veya anahtar bulunmaz.

## Tarayıcıdan doğrudan GitHub bağlantıları

Bunlar backend GitHub REST çağrısı değildir. Kullanıcının tarayıcısı GitHub sayfasını veya görselini açar.

| Tetikleyici | Kaynak | Hedef | Otomatik mi? |
|---|---|---|---|
| “GitHub ile devam et” / “GitHub hesabımı bağla” | `frontend/src/components/github-auth.tsx`; iç `POST github/start/` | `https://github.com/login/oauth/authorize` | Düğmeye basıldıktan sonra yönlendirme. Start endpoint'i yalnız adres üretir; GitHub'a sunucu isteği yapmaz. |
| Repo yetkilendirmesi gereken kurulum ekranı | `frontend/src/components/github-onboarding.tsx`; iç `POST projects/github/start/` | `https://github.com/login/oauth/authorize` | Yeni bağlantının kurulum/giriş devamında ekran efekti yönlendirebilir. Yönetim ekranındaki “GitHub bağlantısını yeniden yetkilendir” ise açık kullanıcı aksiyonudur; status canlı grant kontrolü yapmaz. |
| Repo izinlerini seçme/yönetme | `frontend/src/components/github-onboarding.tsx`, `frontend/src/lib/github-onboarding.ts`; adres `projects/views.py: installation_url` | `https://github.com/apps/{app_slug}/installations/new` | Yalnız izin yönetimi düğmesiyle yönlendirme. Yönetim ekranı kendiliğinden GitHub’a gitmez veya repo listesi yüklemez; izinlerden dönünce mevcut liste otomatik yenilenmez, yenileme düğmesi sunulur. |
| Hesap ekranındaki GitHub avatarı | `frontend/src/components/connected-accounts.tsx: ProviderCard` | `https://avatars.githubusercontent.com/...` | Geçerli saklı avatar adresi varsa kart görüntülenirken doğrudan `<img>` isteği. Tarayıcı önbelleği uygulanabilir; REST çağrısı değildir. Referrer gönderilmez, Next görsel proxy'si kullanılmaz. |
| “GitHub profilini görüntüle” | `frontend/src/components/connected-accounts.tsx` | `https://github.com/{username}` | Kullanıcı bağlantıya tıklayınca yeni sekme. Profil verisi bu tıklamadan önce GitHub'dan yeniden sorgulanmaz. |
| Projedeki GitHub repo bağlantısı | `frontend/src/components/projects.tsx`, `frontend/src/lib/projects.ts` | `https://github.com/{owner}/{repo}` | Yalnız API geçerli bir açık repo URL'si döndürürse gösterilen bağlantıya kullanıcı tıklayınca. Bağlantının gösterimi kendi başına GitHub REST çağrısı değildir. |
| GitHub'da kalan izni veya kurulumu kaldırma | `frontend/src/components/account-reset.tsx`, `frontend/src/app/giris/page.tsx` | `https://github.com/settings/applications`, `https://github.com/settings/installations` | Kullanıcı bağlantıya tıklayınca yeni sekme. FIRST bu sayfalarda işlem gerçekleştirmez. |

OAuth'tan FIRST'e dönüş sayfaları (`/accounts/github/login/callback/`, `/github-repo/callback`) kod/state bilgisini FIRST backend'e iletir. Bu tarayıcı sayfaları doğrudan GitHub token API'sini çağırmaz. Başarılı GitHub giriş/kayıt/bağlama `accounts/oauth_response.py` üzerinden `/github-kurulum` akışına devam edebilir.

## Proje okuma ve kaydetme akışı

| Akış / endpoint | GitHub isteği | Kaynakta görülen davranış |
|---|---|---|
| `GET projects/github/status/` | Yok | Yalnız yerel sağlayıcı bağlantısı, saklı App kimlik bilgisi ve yapılandırmaya bakar. `connected`, canlı GitHub erişim garantisi değildir. |
| `GET projects/github/repositories/` | Yalnız ilk başarılı aktarım henüz yoksa | Listeyi hesaba/kimlik bilgisine bağlı `RepositoryCache` içinde saklar. Başarılı boş liste de saklanır; süreye bağlı otomatik yenileme yoktur. İlk aktarım başarısızsa sonraki GET tekrar aktarım deneyebilir. |
| `POST projects/github/repositories/` (`{}`) | Var | Proje paylaşma veya kurulum ekranında “Repo listesini yenile” düğmesi. Başarısızlık önceki başarılı listeyi korur; başarılı yenileme önceki hazırlıkları geçersiz kılar. |
| GitHub App yetkilendirme dönüşü | Token değişimi ve kimlik kontrolü | Callback saklı listeyi ve hazırlanmış önizlemeleri siler. Sonraki liste GET'i yeni bağlantının ilk aktarımını yapar. GitHub kurulum ayarlarından dönüş ise eldeki listeyi kendiliğinden yenilemez. |
| `POST projects/github/preview/` | Yalnız README ve gerekirse token yenileme | Kayıtlı listeden seçilen repo ile `PreparedRepository` hazırlığı oluşturur; tam bu hazırlığa ait tek kullanımlık `preview_token` döner. |
| `POST projects/` | Yok | Aynı kullanıcı/bağlantı/repo için hazırlanmış veriyi ve onaylanan README özetini kaydeder; hazırlığı tüketir. |
| `GET projects/`, `GET projects/mine/`, `GET projects/{id}/` | Yok | Akış, kendi projeleri ve detay FIRST veritabanından okunur. README yeniden alınmaz. |
| `PATCH projects/{id}/` | Yok | Bilgi düzenleme, arşivleme ve yeniden etkinleştirme FIRST kayıtları üzerinden yapılır. |
| `GET me/`, auth/proje config, GitHub kayıt formu ve e-posta doğrulama | Yok | Hesap/oturum/config veya bekleyen kayıt verisi kullanılır; GitHub profilini yeniden çekmez. E-posta gönderiminin SMTP trafiği bu GitHub envanterinin dışındadır. |

Repo liste snapshot'ı ve yayımlanan proje birbirinden ayrıdır. Repo listesini yenilemek mevcut paylaşımı güncellemez; GitHub'daki sonraki isim, açıklama, görünürlük veya README değişiklikleri paylaşıma otomatik taşınmaz. Örneğin sonradan gizliye alınan bir reponun önceden onaylanmış açık bağlantısı FIRST kaydında kalabilir; bağlantıya tıklanınca erişimi GitHub belirler. Özel olarak paylaşılan gizli repo için repo adı/URL'si döndürülmez; sahibinin paylaşmayı onayladığı metin korunur.

`projects/github.py: repository` genel yardımcı işlevi kaynakta bulunur, fakat bu sürümün proje view/snapshot akışları onu çağırmaz. Canlı repo taraması `authorized_repositories` üzerinden ilk aktarım/manuel yenileme ile sınırlıdır.

## Kontrol kapsamı

Kaynak dosyalarındaki dış HTTP çağrıları, bunları çağıran view/helper'lar, route bağlantıları, tarayıcı yönlendirmeleri ve görsel/link öğeleri okundu. GitHub'a istek gönderilmedi; test, lint/typecheck, build veya tarayıcı doğrulaması yapılmadı. Bu belge çalışma zamanı ağ kaydı değildir.
