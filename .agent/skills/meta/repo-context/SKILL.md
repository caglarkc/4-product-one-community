---
name: repo-context
description: Read product scope and repository evidence before planning or implementing FIRST, STEP, INTO, PATH, or their shared integration.
---

# Repo Context

`AGENTS.md`, `.agent/skills/SKILL-MAP.md` ve `.cursor/maps/stack-shared-ai/overview.md` oku. Kapsam için yalnız seçilen ürünün README ve karar belgelerini oku. “1. ürün / birinci ürün” FIRST demektir. `products.md` yalnız ürünler arası işte; `technology.md` yalnız görev ortak teknoloji bağlamını gerektiriyorsa açılır. Tek ürünün teknoloji işi için kendi teknik kararları ve gerçek kaynakları yeterlidir.

FIRST uygulaması `FIRST/backend/` ve `FIRST/frontend/` altındadır; gerçek manifestleri ve kaynakları doğrula. FIRST teknoloji ve auth seçimleri `FIRST/teknik-kararlar.md` ve `FIRST/auth-kararlari.md` içinde kayıtlıdır. Orchestrator'ın Node CLI'sı ürün backend'i seçimi değildir. Kaynak kodu geldiğinde manifest, kilit dosyası, mevcut pattern ve test komutlarını doğrula; olmayan yolları görev scope'una koyma.

Ürün README'si ve güncel karar belgelerini temel al. Özgün fikirle karşılaştırma gerektiğinde `platform-urun-fikirleri.md` içindeki yalnız ilgili ürün bölümünü oku; tek ürün odağında belgenin tamamını yükleme. Önerileri kesin gereksinime dönüştürme. Kritik eksik karar için önce keşif/specification düğümü oluştur; bağımsız yapılabilen işi sürdür.

`discover` katalog üretir; harita yazmaz. Kaynak değiştiğinde haritayı gerçek dosyalarla karşılaştır, güncelledikten sonra `node .orchestrator/bin/orchestrator.mjs map-manifest` ve `discover` çalıştır.
