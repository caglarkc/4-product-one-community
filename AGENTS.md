# Agent Entry — 4-product-one-community

Bu repo FIRST, STEP, INTO ve PATH ürünlerini tek topluluk bağlamında yönetir. Orchestrator ve bütün skill/PM girişleri **proje kökündedir**; ürün klasörlerine kopyalanmaz.

## İlk okuma

1. `.agent/skills/meta/repo-context/SKILL.md`
2. `.agent/skills/SKILL-MAP.md`
3. `.cursor/maps/stack-shared-ai/overview.md`
4. Yalnız görevle ilgili ürün README'si ve karar belgeleri; `.cursor/maps/stack-shared-ai/products.md` yalnız ürünler arası işte okunur.
5. `.agent/rules.md`; teknoloji işinde seçilen ürünün teknik kararları ve gerçek kaynakları; ortak teknoloji haritası yalnız görev gerektiriyorsa okunur.

Ürün kapsamının kaynağı `platform-urun-fikirleri.md` ve `FIRST/README.md`, `STEP/README.md`, `INTO/README.md`, `PATH/README.md` dosyalarıdır. Haritalar başlangıç bağlamıdır; değişiklikten önce gerçek dosyayı doğrula.

## Rol ve PM seçimi

Varsayılan rol uygulayıcı/reviewer/verify'dir. Kullanıcı PM/yönetici istediğinde `.cursor/PM_GIRIS.md` ve `.cursor/skills/project-manager-mode/SKILL.md` okunur.

“PM'yi yalnız FIRST / 1. ürün odaklı başlat” seçimi, okuma ve çalışma kapsamını FIRST ile sınırlar. Ayrıntılı başlangıç kuralları PM skill'indedir; diğer ürünlerin gereksinimlerini otomatik yükleme. Yalnız “öğren ve bekle” isteğinde görev, run veya agent başlatma.

Tek ürünlü, düşük riskli, açık pattern'li yönetim işi hafif PM akışını kullanır. Ürünler/katmanlar arası, high/critical risk, auth/security/API contract/storage/migration, paralel yazım veya resume işi `.agents/skills/orchestrate-project/SKILL.md` + `.orchestrator/SYSTEM.md` run graph'ını kullanır.

Yönetici hedef, sorumluluk, bağımlılık, kabul kriteri ve dosya sahipliğini belirler. Bağımsız ve sınırları belli işleri native alt agentlara devret; aynı dosyaya paralel yazma. Native imkan yoksa render edilmiş handoff kullan. Sabit ürün başına agent kadrosu oluşturma.

Yönetici yetkisi kullanıcının verdiği görev kapsamındadır; geçmiş projedeki yetkiler bu repoya taşınmaz. Platform izinleri ayrı kalır. Dosya değişen her görev sonunda anlamlı commit ve push varsayılandır; kullanıcı istisnası dışında tekrar izin isteme. Ayrıntılar `.agent/rules.md` → Git Teslim Protokolü.

## Skill seçimi

- Frontend uygulama / review: `.agent/skills/frontend/frontend-implementation/SKILL.md`; FIRST için `FIRST/tasarim-dili.md` ve ortak token/UI bileşenleri zorunludur. Diğer ürünlerin sade yerleşim aşaması ayrı karar verilene kadar korunur.
- Implement / review / verify: `.agent/skills/meta/code-implementation-mode/SKILL.md`
- Ürün kapsamı ve FIRST–STEP–INTO–PATH bağlantıları: `.agent/skills/cross/product-boundaries/SKILL.md`
- API, ortak kimlik, yetki ve veri paylaşımı: `.agent/skills/cross/shared-integration/SKILL.md`
- Teknoloji/entegrasyon kararlarının keşfi: `.agent/skills/meta/repo-context/SKILL.md` + teknoloji haritası.

FIRST için Python/Django/DRF backend ve TypeScript/React/Next.js frontend seçildi; yayın Hetzner/Docker ve Vercel olacak. Kesin kararlar `FIRST/teknik-kararlar.md` ve `FIRST/auth-kararlari.md` içindedir; Django/DRF backend ve Next.js frontend uygulaması mevcuttur. Immense'in Flutter/Node/admin varsayımları burada geçerli değildir. Uygulama kodu geldiğinde gerçek manifest ve kaynakları temel al.

## Kontrol tercihi

Varsayılan olarak yalnız kaynak kodu/diff incele. Kullanıcı açıkça istemedikçe test yazma/çalıştırma, lint/typecheck veya browser/computer use doğrulaması yapma; alt agentlara da aynı sınırı aktar. Ayrıntı: `.agent/rules.md` → Kontrol tercihi.

## Teslim

`.agent/skills/meta/code-implementation-mode/SKILL.md` içindeki beş başlık: yapılan iş, değişen dosyalar, aktif davranışlar, beklenen eklemeler, manuel kontrol. Çalıştırılan kontrolleri ve doğrulanamayan noktaları belirt.
