# FIRST — Teknik kararlar

Kayıt tarihi: 17 Eylül 2026. Kaynak: 16–17 Eylül görüşmesi. Bu belge kabul edilmiş seçimleri kaydeder; kurulum veya uygulama yapıldığı anlamına gelmez.

## Kesinleşen seçimler

| Konu | Karar |
|---|---|
| Platform | Web sitesi yeterli; ayrı mobil uygulama planlanmadı. |
| Ürün sunumu | FIRST, STEP, INTO ve PATH ayrı siteler olacak. |
| Hesaplar | İleride dört üründe ortak hesap kullanılacak. |
| Backend | Python + Django + Django REST Framework. |
| Backend yayını | Hetzner üzerinde Docker. |
| Frontend | TypeScript + React + Next.js. |
| Frontend yayını | Vercel; backend'den ayrı geliştirilecek. |
| Öncelik | Ham işlem hızından önce güvenlik, sağlamlık, veri tutarlılığı ve bakım kolaylığı. |

Kullanıcı “bu dillere ve frameworklere karar verdik” diyerek seçimi onayladı. Django'nun hazır yönetim ve kullanıcı altyapısı ile FIRST'ün ilan/ekip/başvuru ağırlıklı yapısına uygunluğu; Next.js'in açık keşif sayfaları ve Vercel desteği seçim görüşmesinin gerekçeleriydi. TypeScript + NestJS backend alternatifi konuşuldu, seçilmedi.

## Sorumluluk paylaşımı — konuşulan yaklaşım

- Next.js arayüzü ve sayfaların hazırlanmasını, Django iş kurallarını, yetkilendirmeyi, veri işlemlerini ve GitHub entegrasyonunu üstlenecek şekilde ilerlenmesi önerildi.
- Ayrı siteler ve ortak hesap kararı, ortak veritabanı veya tek backend kararı değildir. Ürünler arası oturum/SSO, servis sınırları ve domain yapısı henüz tasarlanmadı.
- Veritabanı, dosya saklama, iş kuyruğu, önbellek, arama altyapısı, sürümler, auth kütüphanesi ve session/JWT seçimi kesinleşmedi.
- Hiçbir sağlayıcı hesabı açılmadı veya ücretli abonelik başlatılmadı.

## API tasarımının ilerleme biçimi

Kullanıcı, bütün API'leri tek seferde gruplandıran uzun listeyi fazla karmaşık buldu. Akış akış ilerleme kararı alındı: önce kayıt/giriş ve hesap bağlantısı, sonra repo bağlama ve ilan oluşturma, düzenleme/görüntüleme, keşif, başvuru/davet ve diğer akışlar. Önceki kapsamlı API listesi onaylanmış endpoint sözleşmesi değildir.

- İlk akışın kabul edilmiş kuralları: [auth-kararlari.md](auth-kararlari.md).
- Öğrenci doğrulama araştırması: [ogrenci-dogrulama-arastirmasi.md](ogrenci-dogrulama-arastirmasi.md).
- Genel ürün kapsamı: [kararlar.md](kararlar.md).

## ADR durumu

Şu aşamada Markdown karar kaydı yeterli kabul edildi. İleride önemli mimari seçimler için gerekçe, alternatif ve sonuç içeren ADR yazılması yaklaşımı benimsendi; her ürün kuralı için ayrı ADR gerekmiyor.
