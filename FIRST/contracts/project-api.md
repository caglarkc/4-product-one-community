# FIRST proje sınıflandırma sözleşmesi

20 Eylül 2026. Temel yol `/api/auth/projects/`. Mevcut Bearer oturumu, session-bound CSRF, e-posta/GitHub doğrulaması, repo yönetim yetkisi ve proje sahipliği koşulları korunur.

## Katalog

`GET config/` anonim erişilebilir. `categories` üst kategorileri ve her birinin `subcategories` seçeneklerini; `stages` proje aşamalarını verir. Her seçenek `value` ve `label`, aşamalar ayrıca `description` taşır. `github_app_enabled` korunur.

Kanonik kod kataloğu `backend/projects/taxonomy.py`, kullanıcı tarafından okunabilir tam liste [proje-kategorileri.md](../proje-kategorileri.md) içindedir. Frontend etiket veya kategori listesi kopyalamaz.

## Proje verisi

Mevcut alanlara ek olarak `subcategory`, `stage`, `category_label`, `subcategory_label`, `stage_label` döner. `category` üst kategori kodudur. Kodlar ASCII kebab-case ve en fazla 40 karakterdir. Etiketler DB'de saklanmaz, katalogdan türetilir.

`POST /api/auth/projects/` için `category`, `subcategory` ve `stage` zorunludur. Alt kategori seçilen üst kategoriye ait olmalıdır. Başlık, repo seçimi, açıklama ve README özeti sözleşmesi değişmez. Bilinmeyen veya uyumsuz sınıflandırma 400 alan hatasıdır.

`PATCH {id}/` kısmi güncellemedir. Gönderilmeyen alanlar korunur. Kategori çifti değiştirilirken gönderilen ve mevcut değerler birleştirilip, güncel proje satırı kilitlendikten sonra birlikte doğrulanır. Üst kategori değişikliği eski alt kategori yeni üstte geçerli değilse yeni alt kategori gerektirir. Salt arşivleme sınıflandırmayı değiştirmez.

`stage` proje sahibinin beyan ettiği geliştirme aşamasıdır. `is_active` yalnız FIRST paylaşımının aktif/arşiv durumudur; uygulamanın gerçekten yayında veya test edilmiş olduğunu göstermez.

## Şema

Mevcut `category` sütunu korunur. Yeni `subcategory` ve `stage` sütunları için additive migration hazırlanır. Eski initial migration değiştirilmez. Kullanıcının mevcut proje bulunmadığı bilgisi nedeniyle veri dönüştürme/backfill işlemi tasarlanmamıştır; Kullanıcı 20 Eylül 2026 tarihinde yalnız gerekli şema migration’ının dağıtımda uygulanmasını onayladı.

## Topluluk ana sayfası — 20 Eylül 2026

`GET /api/auth/projects/?page=N`, giriş gerektirmeden tüm aktif sahiplerin aktif paylaşımlarını en yeni oluşturulandan başlayarak listeler. Sayfa varsayılanı 1, sabit sayfa boyutu 12'dir. Yanıt `projects`, `count`, `next_page`, `previous_page` taşır; son/ilk sayfada ilgili sayfa değeri `null` olur. Geçersiz sayfa değeri 400'dür.

Liste özeti yalnız `id`, `title`, `description`, üç sınıflandırma kodu/etiketi, `created_at` ve `updated_at` içerir. Hesap bilgileri, repo kimliği/adı/URL/gizlilik durumu ve README listede bulunmaz. Listeleme GitHub çağrısı yapmaz; mevcut detay ekranı repo verisini kendi güncel yetki kontrolünden sonra verir. Bu ekleme için şema migration'ı yoktur.

## Liste yükleme bağımlılıkları — 20 Eylül 2026

Ana sayfa istemcisi public listeyi oturum kuyruğundan bağımsız, Authorization olmadan alır; oturum anahtarı okuma/yazma yapmaz. Sayfa değişiminde eski isteği iptal eder. Kimlik doğrulamalı işlemlerin mevcut sıra ve kimlik koruması korunur.

`GET mine/` kimlik doğrulaması ve sahip filtresiyle yalnız kayıtlı proje alanlarını verir; artık GitHub repo taraması yapmaz. Yanıt şekli korunur, ancak canlı kanıt alınmadığından repo adı/URL `null`, `is_private=true` güvenli varsayılandır. Bu değer listede gerçek repo gizliliği iddiası olarak gösterilmez. Mevcut proje detayı repo verisini güncel GitHub erişim kontrolüyle sunmayı sürdürür.
