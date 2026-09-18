---
name: code-implementation-mode
description: Implement, review, or verify scoped changes in the four-product repository using product evidence and the established run result contract.
---

# Implement / Review / Verify

Görevde rolü açık belirt. Ön analiz: **Ne istendi? Dosyalar/ürünler? Riskler? Güncellemeler?** İlgili ürün belgesi, `.agent/rules.md` ve görev skill'lerini oku.

Frontend dosyası değişiyorsa `.agent/skills/frontend/frontend-implementation/SKILL.md` oku; seçilen ürünün tasarım aşamasına uy. FIRST'te `FIRST/tasarim-dili.md`, merkezi token'lar ve ortak UI bileşenleriyle mevcut işlevleri birlikte koru.

## Implement

Yalnız görev-owned dosyaları değiştir. Kullanım ilişkisini ürün sınırlarıyla karşılaştır. Framework, API veya storage kararı kanıtlanmamışsa keşif çıktısı olarak belirt; rastgele stack kurma. Mevcut kod varsa onun pattern'ini kullan. Ortak sözleşmeyi paralel tüketici işlerinden önce netleştir.

## Review

Read-only incele; dosya ve somut etkiyle P0/P1/P2 bulgularını yaz. Özellikle ücretsiz katkı/ücretli iş ayrımı, mentorun kabulü ve ürünler arası erişim sınırlarını kontrol et. Implementer'ın beyanını kanıt sayma.

## Verify

Acceptance maddelerini gerçek çıktı/kontrol ile eşleştir. Çalıştırılmayan kontrolü `not_verified` olarak belirt. Mevcut testleri değişikliğe göre seç; uygulama kodu yokken uygulama testleri geçti deme. Orchestrator değişikliği için `verify-system` ve mevcut Node testlerini çalıştır.

## Git teslimi

Dosya değişen her görev sonunda `.agent/rules.md` Git Teslim Protokolü uygulanır: kontrollerin ardından anlamlı commit ve push yap. Çoklu agent işinde teslimi entegrasyon sahibi ana agent yapar. Açık kullanıcı istisnasını koru; finalde hash ve push sonucunu belirt.

## Required Output Format

1. Yapılan iş (kısa)
2. Değişen dosyalar (değişen ve yeni)
3. Aktif davranışlar
4. Beklenen eklemeler (yoksa Yok)
5. Manuel kontrol (çalıştırılan kontroller ve doğrulanamayanlar dahil)

Run kullanılıyorsa `.orchestrator/contracts/result.schema.json` ile evidence üret. Eksik kanıt uydurma; başarısız denemeyi koru ve revision düğümü kullan.

## FIRST dağıtım teslimi

`.agent/rules.md` → FIRST yayın teslim protokolünü uygula. Backend değiştiğinde gerekli kontrollerden sonra ana agent commit/push, uzak root SSH checkout’unda `git pull --ff-only`, aynı commit’ten Docker rebuild ve canlı sağlık kontrolünü tamamlar. Frontend push ile Vercel otomatik build alır; ek yerel üretim build’i veya manuel Vercel deployment yapma. Test/lint/typecheck ve otomatik dağıtım sonucunu doğrula. Belge/skill değişikliği tek başına backend rebuild gerektirmez; açık kullanıcı istisnası önceliklidir. İşlem ayrıntıları `FIRST/deployment.md` içindedir.
