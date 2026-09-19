---
name: frontend-implementation
description: Implement or review frontend pages in this repository using the selected product's design rules, shared tokens and reusable UI components; preserve real workflows and accessibility.
---

# Frontend uygulama ve ortak tasarım dili

## FIRST — tasarım aşaması açık

18 Eylül 2026 kullanıcı kararı önceki tasarım ertelemesini **FIRST için** kaldırır. FIRST frontend işi öncesi repo kökünden `FIRST/tasarim-dili.md` oku. Onaylanan referansın renkleri ve genel hissi temel alınır; görseldeki yerleşim, içerikler ve henüz uygulanmamış özellikler onaylanmış sayılmaz.

- Kırık beyaz, mürekkep, orman yeşili, adaçayı ve ölçülü mercan paletini; ferah, sakin ve okunabilir yaklaşımı koru.
- Renk, yazı ölçeği, boşluk, kenarlık, köşe, gölge ve odak değerlerini `FIRST/frontend/src/app/tokens.css` içinde semantik CSS değişkenleriyle merkezileştir. Yeni sayfada aynı değerleri tekrar yazma; önce mevcut token'ı kullan, gerçek ihtiyaç varsa ortak tanımı genişlet.
- Buton, aksiyon bağlantısı, form alanı, select, checkbox, uyarı ve yüzey gibi tekrar eden öğelerde `FIRST/frontend/src/components/ui/` altındaki ortak bileşenleri kullan. Native HTML prop'larını, erişilebilirliği ve form davranışını koru. Buton varyantı ve durumu bir yerde tanımlansın; sayfaya özel buton CSS'i veya kopya bileşen üretme.
- Sayfalar sadece akışa özgü düzen ve içeriği birleştirir. Ortak görsel değişiklik token/bileşende yapılır. Yeni varyantı benzer öğelerin tümüne uygula; tek bir sayfayı ayrı tema haline getirme.
- Tasarım mevcut işlevlere uyarlanır: gerçek route, alan, uyarı, validasyon, yüklenme ve başarı/hata durumlarını koru. Sırf referansta var diye proje kartı, arama, keşif, ekip veya diğer yeni ürün işlevlerini ekleme.
- Mevcut HTML/CSS ve React ile çözülebilen işler için yeni UI, ikon veya animasyon bağımlılığı ekleme. Dekorasyon içerikle yarışmasın; mobilde alan ve okuma sırası korunsun.

## Diğer ürünler

STEP, INTO ve PATH için ayrı tasarım kararı verilene kadar 17 Eylül 2026 işlev ve sade yerleşim önceliği korunur. FIRST paletini veya kapsamını bu ürünlere otomatik taşıma.

## Ortak işlev ve doğrulama

- Görünür etiket, klavye odağı, yeterli kontrast, hata/başarı/yüklenme durumları ve form doğrulaması tasarımın parçasıdır. Kullanıcı ne yapacağını ve işlemin sonucunu anlayabilmelidir.
- Gerçek API'ye bağlı akışları kullan; mock başarıyı çalışan entegrasyon gibi gösterme. Sağlayıcı ayarı eksikse işlemi başarıyla tamamlanmış gösterme.
- Teknik altyapıyı ilgili ürünün gerçek manifesti ve karar dosyalarından doğrula. FIRST için `FIRST/teknik-kararlar.md`, auth için `FIRST/auth-kararlari.md` kaynak kabul edilir.

Review/verify yalnız kaynak kodu okuyarak yapılır; kullanıcı istemedikçe tarayıcı açma, computer use kullanma veya test/lint/typecheck çalıştırma. FIRST'te token ve bileşen tekrar kullanımı, sayfalar arası tutarlılık, kontrast, odak, disabled/loading/error/success durumları, masaüstü ve dar ekran görünümü ile mevcut işlevleri birlikte kontrol et. Görsel referansı yerleşim şartnamesi olarak kullanma. Diğer ürünlerde henüz açılmamış görsel tasarımı eksik özellik sayma. Çalıştırılan kontroller ile doğrulanamayanları ayır.

## FIRST dağıtım teslimi

`.agent/rules.md` → FIRST yayın teslim protokolünü uygula. Backend değiştiğinde gerekli kontrollerden sonra ana agent commit/push, uzak root SSH checkout’unda `git pull --ff-only`, aynı commit’ten Docker rebuild ve canlı sağlık kontrolünü tamamlar. Frontend push ile Vercel otomatik build alır; ek yerel üretim build’i veya manuel Vercel deployment yapma. Varsayılan kontrol yalnız kaynak kod incelemesidir; kullanıcı istemedikçe test/lint/typecheck veya browser/computer use doğrulaması yapma. Mevcut dağıtım komutunun sonucunu raporla. Belge/skill değişikliği tek başına backend rebuild gerektirmez; açık kullanıcı istisnası önceliklidir. İşlem ayrıntıları `FIRST/deployment.md` içindedir.
