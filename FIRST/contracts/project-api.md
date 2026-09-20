# FIRST proje ve repo aktarım sözleşmesi

20 Eylül 2026. Temel yol `/api/auth/projects/`. FIRST oturumu, CSRF ve sahiplik kontrolleri korunur. Kullanıcının son kararıyla **yayımlanmış projeler GitHub'dan bağımsız kayıtlı kopyalardır**; önceki canlı repo doğrulamalı detay davranışı kaldırılmıştır.

## Katalog ve sınıflandırma

`GET config/` anonim erişilebilir; `categories` üst kategoriler ve her birinin `subcategories` seçenekleri, `stages` ise `value`, `label`, `description` verir. `github_app_enabled` korunur. Kanonik kaynak `backend/projects/taxonomy.py`, okunabilir liste [proje-kategorileri.md](../proje-kategorileri.md).

`category`, `subcategory`, `stage` oluşturma sırasında zorunludur. Alt kategori seçilen üste ait olmalıdır; bilinmeyen/uyumsuz seçim alan hatasıdır. Kodlar en çok 40 karakterdir. Yanıt ayrıca katalogdan türetilen `category_label`, `subcategory_label`, `stage_label` içerir.

## Repo listesinin kalıcı kaydı

- `GET github/status/` yalnız yerel yapılandırma ve kayıtlı App kimlik bilgisi durumunu verir. `connected`, GitHub'dan canlı doğrulama yapıldığı anlamına gelmez.
- `GET github/repositories/` kullanıcıya bağlı kayıtlı repo listesini döndürür. Kayıt yoksa ilk GitHub içe aktarımını yapar. Boş liste de geçerli kayıttır; süre dolunca otomatik yenileme yoktur.
- `POST github/repositories/` gövde `{}` ile açık yenilemedir. GitHub'dan yeniden alınır, başarıda kayıtlı liste atomik değiştirilir. Hata önceki listeyi silmez.
- Yanıt `{repositories, cached_at}`. Kimlik/kurulum ve yönetim yetkisi liste GitHub'dan alındığında doğrulanır. Kayıt yalnız ilgili kullanıcı/credential için erişilebilirdir.
- Credential silinmesi bağlı liste ve hazırlanan kopyaları siler. App yeniden yetkilendirmesi eski kopyaları geçersiz kılar. Eski bir ağ yanıtı yeni yenilemeyi veya koparılan bağlantıyı geri getiremez.

## Hazırlama ve oluşturma

`POST github/preview/` seçilen `installation_id`, `repository_id` ile kayıtlı listedeki repo verisini kullanır. Kullanıcının “Paylaşımı hazırla” aksiyonunda README özeti bir kez GitHub'dan alınır; bu proje oluşturulmadan önceki içe aktarım adımıdır. Repo listesi bu adımda yeniden taranmaz. Sunucu exact repo/gizlilik/README kopyasını kaydeder; yanıt `{repository, readme_excerpt, preview_token}`.

`POST /api/auth/projects/`: repo seçim kimlikleri, `preview_token`, başlık, sınıflandırma ve isteğe bağlı açıklama/README özeti gönderilir. Kaydetme GitHub'a gitmez. Sunucu ilgili kullanıcıya ait tam hazırlanan kopyayı doğrular ve tek kullanımlık token'ı tüketir. README yalnız boş veya hazırlanmış metinle aynı olabilir. Yeniden hazırlama/başarılı liste yenilemesi eski onayı geçersiz kılar; eski token yeni repo verisine sessizce uygulanmaz.

Projeye repo adı/URL, oluşturma anındaki gizlilik ve onaylanan metin kaydedilir. Gizli repo adı/URL'si proje yanıtında verilmez. Açık repo bağlantısı kayıtlı kopyadan gelir; GitHub'daki sonraki değişiklikler otomatik uygulanmaz.

## Okuma ve düzenleme

`GET {id}/`, `GET mine/` ve public liste yalnız FIRST verisini okur; GitHub ağına çıkmaz. Detayda arşivlenmiş proje yalnız sahibine görünür. Kayıtlı README özeti, paylaşım sırasında onaylanan içeriktir. Eski projelerde daha önce saklanmamış repo adı/URL boş kalır; bunu doldurmak için otomatik GitHub isteği yapılmaz.

`PATCH {id}/` sahibin kısmi güncellemesidir; mevcut FIRST oturumu ve gereken e-posta koşulu korunur, GitHub bağlantısı/isteği gerekmez. Eksik sınıflandırma alanları kilitli güncel proje değerleriyle birleştirilerek doğrulanır. Salt arşivleme sınıflandırmayı değiştirmez. Repo snapshot alanları istemci tarafından serbestçe değiştirilemez. `stage` proje sahibinin beyan ettiği aşama, `is_active` FIRST paylaşımının aktif/arşiv durumudur.

## Topluluk listesi

`GET /api/auth/projects/?page=N` tüm aktif sahiplerin aktif paylaşımlarını en yeni önce sıralar; varsayılan sayfa1, sabit boyut12. Yanıt `projects`, `count`, `next_page`, `previous_page`. Özet yalnız id/başlık/açıklama, sınıflandırma kodları/etiketleri ve tarihlerdir; repo, README ve hesap verileri içermez. Ana sayfa bu endpoint'e anonim, oturum kuyruğundan bağımsız gider ve eski isteği sayfa değişiminde iptal eder.

## Şema ve GitHub çağrıları

0002 sınıflandırma alanlarını; 0003 repo adı/URL kopyası, kalıcı envanter ve hazırlanmış repo kayıtlarını ekler. Eski migration'lar değiştirilmez, GitHub'dan veri backfill yapılmaz. Kalan dış bağlantıların tam listesi [github-connections.md](github-connections.md).
