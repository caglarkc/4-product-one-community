# 4-product-one-community

Dört ürünün fikir, kapsam ve mevcut kararları:

- [FIRST — Future Innovators Research & Source Team](FIRST/README.md)
- [STEP — Student Talent Entry Platform](STEP/README.md)
- [INTO — Industry Navigation & Talent Orientation](INTO/README.md)
- [PATH — Problem Arena for Talent & Hiring](PATH/README.md)

Tüm ürünleri içeren özgün notlar: [Platform ürün fikirleri](platform-urun-fikirleri.md).

## Ortak agent / orchestrator yapısı

Dört ürün tek kök orchestrator kullanır. Başlangıç: [AGENTS.md](AGENTS.md). İşleyiş ve komutlar: [.orchestrator/SYSTEM.md](.orchestrator/SYSTEM.md). Skill seçimi: [.agent/skills/SKILL-MAP.md](.agent/skills/SKILL-MAP.md). Teknoloji durumu: [technology.md](.cursor/maps/stack-shared-ai/technology.md).

```sh
node .orchestrator/bin/orchestrator.mjs discover
node .orchestrator/bin/orchestrator.mjs verify-system
node --test .orchestrator/test/orchestrator.test.mjs
```

Yeni kapsamlı görev (repo kökünden):

```sh
node .orchestrator/bin/orchestrator.mjs new --id integration-prep --title "Entegrasyon hazırlığı" --goal "Ürün kapsamı ve ortak entegrasyon sözleşmelerini netleştir"
```

Bu komut boş draft run oluşturur; manager gerçek görevleri ve kabul kriterlerini ekler. Ürün uygulaması veya dış AI servisi başlatmaz. Yapı Immense'den uyarlanmıştır; ürün teknoloji seçimleri henüz kesinleşmemiştir.
