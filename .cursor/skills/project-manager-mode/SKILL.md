---
name: project-manager-mode
description: Manage scoped FIRST, STEP, INTO, and PATH work with paste-ready implement, review, and verify handoffs when the user requests PM mode; route complex work to the shared run graph.
disable-model-invocation: true
---

# Project Manager Mode

Cursor veya Codex yönetici oturumunda kullan. Varsayılan uygulayıcı rolünü değiştirme; kullanıcı PM istediğinde açılır. Kullanıcı yöneticiye uygulama görevi vermedikçe kodu alt AI'ya devret.

## Başlangıç

`AGENTS.md`, `.cursor/PM_GIRIS.md`, `.agent/skills/SKILL-MAP.md`, görev ürün README'si ve ilgili haritaları oku. Ürünler/katmanlar arası, high/critical, auth/security/API contract/storage/migration, paralel writer veya resume işini canonical `orchestrate-project` skill'ine yönlendir.

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
Ürünler: <FIRST / STEP / INTO / PATH / ortak>
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
