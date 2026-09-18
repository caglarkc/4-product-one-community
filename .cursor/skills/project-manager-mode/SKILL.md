---
name: project-manager-mode
description: Manage requested product work in PM mode, including a FIRST-only (1st product) start with scoped context; route complex work to the shared run graph.
disable-model-invocation: true
---

# Project Manager Mode

Cursor veya Codex yönetici oturumunda kullan. Varsayılan uygulayıcı rolünü değiştirme; kullanıcı PM istediğinde açılır. Kullanıcı yöneticiye uygulama görevi vermedikçe kodu alt AI'ya devret.

## Başlangıç

Önce kullanıcının ürün seçimini belirle; `AGENTS.md`, `.cursor/PM_GIRIS.md`, `.agent/skills/SKILL-MAP.md`, `.agent/rules.md` ve yalnız seçilen ürünün belgelerini oku. Ürün belirtilmemişse yalnız PM yöntemini öğren; bütün ürün gereksinimlerini yükleme. Somut görevde ürün bağlamdan çıkarılamıyorsa ürün seçimini sor.

### Yalnız FIRST / 1. ürün başlangıcı

- “PM'yi sadece FIRST için başlat”, “PM manager skill'ini birinci ürün odaklı öğren” ve “yalnız 1. üründe çalış” ifadeleri aynı seçimi yapar: **aktif ürün FIRST**. Bu seçim kullanıcı değiştirene kadar sonraki görev ve handoff'larda korunur.
- Başlangıç gereksinimleri için `FIRST/README.md` ve `FIRST/kararlar.md` oku. Teknik görevde `FIRST/teknik-kararlar.md`, kayıt/giriş görevinde `FIRST/auth-kararlari.md` ve ilgili gerçek kaynak/sözleşmeleri ihtiyaç oldukça aç. README'deki bütün bağlantıları peşinen takip etme.
- STEP, INTO ve PATH belgelerini, `products.md` haritasını veya `platform-urun-fikirleri.md` dosyasının tamamını yükleme. FIRST belgelerinde diğer ürünlerin anılması tek başına kapsamı genişletmez. Gerekli ürün sınırını önce FIRST belgelerinden öğren.
- Çalışma kapsamı FIRST'tür; ortak dosyalarda yalnız FIRST görevinin gerektirdiği değişiklikleri yap. Görev açıkça ürünler arası entegrasyon istiyorsa yalnız ilgili ek ürün bağlamını oku. FIRST görevi sırasında böyle bir ihtiyaç ortaya çıkarsa gerekçesini belirt ve kapsam genişletme kararını kullanıcıya bırak; bağımsız FIRST işini sürdür.
- “Öğren ve bekle” denildiyse okumadan sonra aktif kapsamı kısaca bildir ve bekle; run oluşturma, agent başlatma veya dosya değiştirme.

Örnek: **“PM manager skill'ini sadece 1. ürün (FIRST) odaklı öğren ve bekle.”**

Ürünler/katmanlar arası, high/critical, auth/security/API contract/storage/migration, paralel writer veya resume görevini canonical `orchestrate-project` skill'ine yönlendir. Bu geçiş aktif ürün seçimini değiştirmez: yalnız FIRST işinde diğer ürünlerin kapsam belgeleri ve ürünler arası sınır skill'i varsayılan okuma değildir. Gerekli review/verify kapıları korunur.

## Hafif akış

1. Hedefi ve tek iş kapsamını çıkar; yolları dosyadan doğrula.
2. Implement promptunu hazırla. Aktif platformun native imkanını kullan; yoksa paste-ready handoff ver. Kullanıcının platform tercihini koru.
3. Sonucu kapsam, ürün sınırları, dosya sahipliği ve acceptance kanıtlarıyla karşılaştır.
4. Review ve verify ihtiyacını riske göre seç. Zorunlu gate gerektiren işi graph'a taşı.
5. Eksik/yanlış sonuçta yalnız bulguları hedefleyen revision promptu üret. Başarısız denemeyi kaybetme.
6. Kararı KABUL / REVİZE / DEVAM / SORU ve sonraki somut adımla kısa özetle.

## Ortak handoff

```text
[GÖREV] <tek amaç>
Rol: IMPLEMENT | REVIEW | VERIFY | SPEC
Repo: 4-product-one-community
Ürünler: <aktif seçim; FIRST odağında yalnız FIRST>
Hedef platform: <aktif veya kullanıcı seçimi>
Okuma: AGENTS.md, .agent/rules.md, ilgili ürün README'si,
.agent/skills/meta/code-implementation-mode/SKILL.md ve görev skill'leri
Girdi: <gerçek path / contract / önceki sonuç>
Yazma kapsamı: <tek sahipli gerçek path'ler; review için yok>
Çıktı: <dosya / bulgu / kanıt>
Kabul: <doğrulanabilir maddeler>
Bağımlılık: <önce tamamlanacak sonuç>
Sınır: <ürün kararı, teknoloji varsayımı, kapsam dışı>
Teslim: code-implementation-mode beş başlık + çalıştırılan kontroller
Git: Dosya değişen görev sonunda ana agent anlamlı commit ve push yapar; .agent/rules.md Git Teslim Protokolü ve açık kullanıcı istisnaları geçerlidir. Alt writer bağımsız push yapmaz.
```

Implement'te mevcut pattern ve ürün kurallarını uygulat. Review'da dosya değiştirmeden P0/P1/P2 ve kanıt iste. Verify'da gerçek çalıştırma/manuel adım ile acceptance eşleşmesini iste; çalıştırılmayanı açık yazdır. Revizyonda önceki bulguyu ve beklenen düzeltmeyi belirt; ilgisiz refactor ekleme.

## FIRST dağıtım teslimi

`.agent/rules.md` → FIRST yayın teslim protokolünü uygula. Backend değiştiğinde gerekli kontrollerden sonra ana agent commit/push, uzak root SSH checkout’unda `git pull --ff-only`, aynı commit’ten Docker rebuild ve canlı sağlık kontrolünü tamamlar. Frontend push ile Vercel otomatik build alır; ek yerel üretim build’i veya manuel Vercel deployment yapma. Test/lint/typecheck ve otomatik dağıtım sonucunu doğrula. Belge/skill değişikliği tek başına backend rebuild gerektirmez; açık kullanıcı istisnası önceliklidir. İşlem ayrıntıları `FIRST/deployment.md` içindedir.
