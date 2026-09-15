---
name: repo-context
description: Read product scope and repository evidence before planning or implementing FIRST, STEP, INTO, PATH, or their shared integration.
---

# Repo Context

`AGENTS.md`, `.agent/skills/SKILL-MAP.md` ve `.cursor/maps/stack-shared-ai/overview.md` oku. Kapsam için yalnız ilgili ürün README'lerini; ürünler arası işte `products.md`; teknoloji işinde `technology.md` haritasını aç.

Şu an uygulama manifesti veya seçilmiş stack yoktur. Orchestrator'ın Node CLI'sı ürün backend'i seçimi değildir. Kaynak kodu geldiğinde manifest, kilit dosyası, mevcut pattern ve test komutlarını doğrula; olmayan yolları görev scope'una koyma.

Ürün kararlarını `platform-urun-fikirleri.md` ile karşılaştır. Önerileri kesin gereksinime dönüştürme. Kritik eksik karar için önce keşif/specification düğümü oluştur; bağımsız yapılabilen işi sürdür.

`discover` katalog üretir; harita yazmaz. Kaynak değiştiğinde haritayı gerçek dosyalarla karşılaştır, güncelledikten sonra `node .orchestrator/bin/orchestrator.mjs map-manifest` ve `discover` çalıştır.
