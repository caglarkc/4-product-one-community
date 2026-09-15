# Mimari — Immense yapısının ürün uyarlaması

Kaynak: `/Users/caglarkc/Desktop/immense/.orchestrator` (15 Eylül 2026 yerel kopyası). Bu çalışma yeni orkestrasyon tasarımı değildir.

## Korunan yapı

- Yönetici model + paket bağımlılığı olmayan Node CLI.
- Dinamik görev rolleri; tek kök JSON run grafiği ve append-only JSONL geçmiş.
- Aynı lifecycle, run/result/event şemaları, risk politikası ve review/verify/revision/integration ilişkileri.
- Aynı bağımlılık/yazma kapsamı scheduler'ı, lock/revision kontrolleri ve evidence kabul mekanizması.
- Aynı Codex/Cursor/Claude Code adaptörleri, native-first yaklaşım ve render edilmiş handoff.
- Canonical `.agents/skills` girişi; `.agent` görev skill'leri; hafif `.cursor` PM akışı; `CLAUDE.md` köprüsü.

## Repo uyarlamaları

- `config.json` ürün belgelerini sourceRoots olarak izler; sistem adı güncellendi.
- `src/core.mjs` içindeki iki repo katmanı listesi FIRST/STEP/INTO/PATH olarak değiştirildi. Manifest generator etiketi `manual-product-context` oldu. Algoritmalar değişmedi. Ürünler arası/ortak dosya işinde manager ayrıca `requiresIntegration: true` belirtir.
- Framework'e bağlı skill'ler yerine mevcut ürün sınırları, ortak entegrasyon ve teknoloji keşfi bağlamı yerleştirildi. Teknoloji seçilmiş gibi gösterilmedi.
- Immense'e özgü servis başlatma yasakları ve geçmiş Git yayın yetkisi taşınmadı. Bu projenin kullanıcısı ayrıca dosya değişen her görev sonunda anlamlı commit/push için kalıcı talimat verdi; `.agent/rules.md` Git Teslim Protokolü uygulanır. Manager run kararı platform izinlerini değiştirmez.
- Üç örneğin graph yapıları korundu; ürün yolları ve bağlamları uyarlandı. Örnek results/events sentetiktir. Gerçek Immense run'ları/katalogları taşınmadı.
- CI yalnız taşınan orchestrator kontrollerini çalıştırır; Immense'e özel map/credential script'leri bu repoda yoktur.

Adaptörler kaynak yapının taşınmış rehberidir; güncel oturumda araç kullanılabilirliğini garanti etmez. Araçlar oturumdan doğrulanır. Yeni daemon, framework, model ayarı, sabit agent kadrosu veya ürün başına orkestratör eklenmedi.
