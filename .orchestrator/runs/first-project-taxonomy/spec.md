# FIRST iki seviyeli kategori ve geliştirme durumu

## Ürün modeli

Üst kategori projenin ana çıktısını/türünü, alt kategori kullanım amacını belirtir. Alt kategoriler üst kategoriye özeldir. Teknoloji, programlama dili, repo görünürlüğü ve geliştirme durumu kategori değildir. Bir proje bir üst kategori ve o üst kategoriye ait bir alt kategori seçer.

Proje durumu ayrı, kullanıcı tarafından seçilen altı geliştirme aşamasıdır: Fikir ve Planlama, İlk Prototip, Aktif Geliştirme, Yayına Hazırlık, Yayın Öncesi Test, Yayında ve Geliştiriliyor. Platform bu aşamaları doğruladığını iddia etmez. Proje aşaması ile FIRST paylaşımının aktif/arşiv durumu ayrı gösterilir.

## Veri/API sözleşmesi

- Mevcut `category` alanı üst kategoriyi saklamaya devam eder.
- `subcategory` ve `stage` yeni string alanlardır; oluşturma isteğinde üç seçim de zorunludur.
- Kanonik kaynak `FIRST/backend/projects/taxonomy.py`: `CATEGORIES` (value, label, subcategories), `STAGES` (value, label, description). Frontend katalog kopyası tutmaz.
- GET `projects/config/`: `categories` artık iç içe subcategories listesini içerir; `stages` eklenir. github_app_enabled korunur.
- Proje yanıtı category/subcategory/stage kodları ve category_label/subcategory_label/stage_label insan tarafından okunabilir etiketlerini içerir. Etiketler backend kataloğundan türetilir, DB'ye kopyalanmaz.
- POST `projects/` ve PATCH `projects/{id}/` seçimleri backend'de doğrular. Alt kategori seçilen üst kategoriye ait olmalıdır; bilinmeyen kod kabul edilmez.
- PATCH'te eksik alanlar mevcut değerle birleştirilir. Birleştirilmiş üst/alt kategori çifti kilit altında güncel proje üzerinde doğrulanır. Sadece arşivleme diğer alanları değiştirmez; GitHub/email/sahiplik koşulları korunur.

## Arayüz

Formda Üst kategori, Alt kategori ve Proje durumu alanları bulunur. Üst kategori seçilene kadar alt alan devre dışıdır. Üst değişince alt seçim ve paylaşım onayı sıfırlanır. Durumun kısa açıklaması seçime göre gösterilir. Düzenleme mevcut değerleri yükler. Liste ve detay, iki kategori etiketini ve proje aşamasını gösterir; paylaşım görünürlüğü ayrı olarak “Paylaşım aktif / Arşivde” şeklinde adlandırılır.

## Şema ve teslim sınırı

Kullanıcı mevcut proje olmadığını ve DB migration çalıştırmaya gerek olmadığını belirtti. Mevcut projeler tablosu bulunduğundan iki sütun için yine şema değişikliği gerekir; veri taşıma gerekmez. Kullanıcı 20 Eylül 2026 tarihinde “Yalnız gerekli şema migration’ını uygula” seçeneğini açıkça onayladı. Dağıtımda yalnız iki sütunu ekleyen AddField migration uygulanır; veri dönüştürme yapılmaz. Geçmiş initial migration değiştirilmez ve şema dışı paketlenmiş string/JSON geçici çözümü uygulanmaz.

Kaynak/diff kontrolü; test/lint/typecheck/browser yok. API/model değişiklikleri bağımsız review ve verify alır. Çalıştırılmamış davranış doğrulanmış sayılmaz.
