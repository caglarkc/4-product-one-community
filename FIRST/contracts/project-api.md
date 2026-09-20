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
