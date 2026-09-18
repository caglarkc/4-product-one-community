# Skill haritası

Bütün skill'ler proje kökündedir; ürün başına kopya veya kalıcı agent yoktur.

| İş | Skill |
|---|---|
| Bağlam, kapsam ve teknoloji keşfi | `meta/repo-context/SKILL.md` |
| Frontend sayfa/form; FIRST ortak tasarım dili, token ve UI bileşenleri | `frontend/frontend-implementation/SKILL.md` |
| Implement / Review / Verify | `meta/code-implementation-mode/SKILL.md` |
| FIRST, STEP, INTO, PATH iş kuralları | `cross/product-boundaries/SKILL.md` |
| Ürünler arası API/veri/yetki entegrasyonu | `cross/shared-integration/SKILL.md` |
| Kalıcı graph ve delegation | `.agents/skills/orchestrate-project/SKILL.md` (repo kökünden) |
| Hafif paste-ready yönetim | `.cursor/skills/project-manager-mode/SKILL.md` (repo kökünden) |

Kısa göreli yollar `.agent/skills/` altındadır. Görev rolü dinamik seçilir; ayrı implement/review/verify çıktıları aynı skill'in ilgili bölümünü kullanır.

## Ortama bağlı ek skill seçimi

Bunlar repo bağımlılığı veya kurulu olma garantisi değildir. Aktif oturumda varsa ve görev gerektiriyorsa oku:

- UX araştırma/akış inceleme: Product Design; Figma uygulama/tasarım işleri: ilgili Figma skill'i.
- Görsel üretim: imagegen; doküman/PDF/tablo: ilgili artifact skill'i.
- STEP AI asistanının OpenAI ile uygulanması seçilirse: openai-docs.
- Framework, veritabanı, ödeme sağlayıcısı ve test skill'leri: teknoloji seçimi ve gerçek kod geldikten sonra eşleştir.

Immense'in Flutter, fitness/coaching, beslenme, uzak Docker ve admin-panel skill'leri bu ürünlerin mevcut teknoloji kararı değildir; kopyalanmaz.
