---
name: shared-integration
description: Plan and check shared API, identity, project references, and access boundaries across FIRST, STEP, INTO, and PATH without assuming an unchosen stack.
---

# Ortak entegrasyon

Önce `product-boundaries` skill'ini ve `.cursor/maps/stack-shared-ai/technology.md` oku. Görev kapsamındaki entegrasyonun gerçek üretici/tüketici yollarını doğrula.

- Aynı FIRST projesinden INTO mentor arayışına geçerken proje kimliği ve sahipliğini koru; kopya proje akışını varsayma.
- Profil/katkı/takım bilgisinin STEP'e taşınması erişim yetkisini otomatik taşımaz. Hangi verinin hangi role görüneceğini sözleşmede belirt.
- Kapalı repo, mentor erişimi, ücretli iş dosyası ve olası takip kaydı için kaynak, sahibi, okuyan rol ve yaşam döngüsünü belirle. Detay kararlaştırılmamışsa specification işi aç.
- Entegrasyon sözleşmesinde girdi/çıktı, kimlik referansı, yetki, hata, durum geçişleri ve tekrarlanan isteğin etkisini tanımla. Sağlayıcı ve framework yalnız seçilmişse kullan.
- Ödeme, GitHub, takvim/görüşme, AI veya yarışma çalıştırma entegrasyonunu mevcut servis gibi gösterme. Mock ile gerçek servisin doğrulama kanıtını ayır.

Ürünler arası işlerde `policy.requiresIntegration: true` kullan; contract → tüketici/üretici → bağımsız review/verify → integration bağımlılıklarını kur. Ortak dosyalar tek writer'a aittir. Varsayılan review/verify kaynak kodu incelemesidir; test veya browser/computer use yalnız kullanıcı açıkça isterse yapılır. Kaynak incelemesi kabulünü çalışma zamanı test başarısı gibi sunma.
