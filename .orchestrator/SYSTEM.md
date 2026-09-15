# Project Orchestrator

Bu dizin, `4-product-one-community` için platformdan bağımsız yönetim düzlemidir. Kaynak kodu çalıştıran bir daemon değildir; yönetici modelin görevleri güvenli biçimde ayrıştırması, dispatch etmesi, sonuçları kabul/revize etmesi ve kaldığı yerden devam etmesi için sözleşme, geçmiş ve deterministik yardımcı komutlar sağlar.

Ürün bağlamı `.cursor/maps/stack-shared-ai/` ve `.agent/skills/SKILL-MAP.md` üzerinden okunur. Bütün ürünler tek kök sistemi paylaşır. Ürün/ortak katman geçişlerinde `policy.requiresIntegration: true` kullanılır. Örnek run'lar sentetik fixture'lardır; uygulanmış ürün veya gerçek görev geçmişi değildir.

## Sistem sınırı

```text
Kullanıcı hedefi
    ↓
Yönetici model + orchestrate-project skill
    ↓
Run graph (vendor-neutral JSON) ─── Event log (append-only JSONL)
    ↓                                  ↓
Hazır ve çakışmasız batch'ler       Resume / audit
    ↓
Codex | Cursor | Claude Code adapter
    ↓
Native subagent/worktree veya paste-ready handoff
    ↓
Result contract → Review → Verify → Integration → Kabul/Revizyon
```

Sistem dört ilkeye dayanır:

1. **Graph kaynak gerçektir.** Konuşma belleği veya agent'ın “bitti” demesi tamamlanma kanıtı değildir.
2. **Roller dinamiktir.** Kalıcı agent listesi yerine her work item ihtiyaç duyduğu capability ve sorumluluğu tanımlar.
3. **Platform adapter'dır.** Native delegation, worktree, approval ve tool adları run sözleşmesine sızmaz.
4. **Kalite graph düğümüdür.** Review, verify, revision ve integration state değil, bağımlı work item'lardır.

5. **Yönetici verilen görev kapsamında çalışır.** Proje kararları mevcut yetki kapsamında alınır; platform izinleri ayrı kalır. Dosya değişen her görev sonunda `.agent/rules.md` Git Teslim Protokolü uyarınca anlamlı commit ve push yapılır; açık kullanıcı istisnası korunur.

## Dizinler

| Yol | Sorumluluk |
|---|---|
| `config.json` | Repo yolları, lifecycle, risk, paralellik, geçmiş ve guardrail politikaları |
| `contracts/` | Run, event ve result JSON Schema sözleşmeleri |
| `adapters/` | Platform capability, sınır ve fallback bilgisi |
| `bin/orchestrator.mjs` | İnsan/agent tarafından çağrılan CLI |
| `src/core.mjs` | Doğrulama, scheduling, discovery, render ve history çekirdeği |
| `catalog/` | Gerçek dosyalardan üretilen skill/map/capability snapshot'ı |
| `runs/<run-id>/` | `run.json`, `events.jsonl` ve kabul edilen/edilmeyen sonuçlar |
| `examples/` | Küçük, cross-layer ve kritik güvenlik örnekleri |
| `test/` | Çekirdeğin Node built-in testleri |

## Hızlı başlangıç

Repo kökünde:

```powershell
node .orchestrator/bin/orchestrator.mjs discover
node .orchestrator/bin/orchestrator.mjs new --id auth-refresh --title "Auth refresh" --goal "Refresh token akışını güvenli biçimde güncelle"
node .orchestrator/bin/orchestrator.mjs validate .orchestrator/runs/auth-refresh/run.json
node .orchestrator/bin/orchestrator.mjs status .orchestrator/runs/auth-refresh/run.json
```

`new`, boş bir draft run oluşturur. Yönetici model `items` alanını görev gereksinimlerine göre doldurur. Hazır work item için platform prompt'u:

```powershell
node .orchestrator/bin/orchestrator.mjs render .orchestrator/runs/auth-refresh/run.json scope-analysis --platform codex
```

## Work item tasarım kuralları

Her item şu soruları tek başına cevaplamalıdır:

- **Amaç:** Bu iş hangi somut problemi çözüyor?
- **Sorumluluk:** Agent nerede karar verebilir, nerede durmalıdır?
- **Girdi:** Hangi path, contract, önceki artifact veya karar kullanılacak?
- **Çıktı:** Hangi dosya, bulgu, plan, diff veya kanıt üretilecek?
- **Kabul:** “Bitti” demek için hangi doğrulanabilir koşullar sağlanacak?
- **Bağımlılık:** Hangi sonuçlar olmadan başlayamaz?
- **Kapsam:** Hangi path'leri okuyabilir ve yazabilir?
- **Risk:** Bağımsız review, verify veya insan kararı gerekiyor mu?
- **Execution:** Inline mı, dedicated agent mı; read-only mi; worktree tercihi var mı?

`kind` ve `domains` alanları bilinçli olarak açık uçludur. Sistem yeni görev türlerini tanımak için schema değişikliği istemez. Buna karşılık lifecycle state'leri az ve sabittir; sadece işin yürütme durumunu anlatır.

## Lifecycle

```text
draft → ready → active → done
   └──────┐       ├──→ blocked → ready
          └───────┼──→ failed
                  └──→ cancelled
```

- `draft`: Planlandı, fakat bağımlılık/gate nedeniyle dispatch edilmez.
- `ready`: Tüm `dependsOn` düğümleri `done`; dispatch edilebilir.
- `active`: Bir agent/thread bu item'ın sorumluluğunu aldı.
- `blocked`: Dış karar, approval veya girdi bekliyor; gerekçe event'e yazılır.
- `done`: Result contract acceptance kanıtıyla kabul edildi.
- `failed`: Deneme başarısız; immutable kalır. Düzeltme yeni `revises` item'ıdır.
- `cancelled`: Bilinçli olarak kapsamdan çıkarıldı.

Review, verify, test, integration ve revision bu state listesine eklenmez. Bunlar özgür `kind` değerine sahip normal graph düğümleridir.

## Scheduling ve paralellik

`status` komutu runnable item'ları ve güvenli batch'leri üretir. İki yazan item aynı batch'e ancak `writeScopes` alanları çakışmıyorsa alınır.

- `readOnly: true` item'lar birlikte çalışabilir.
- Boş/`*` write scope, bilinmeyen kapsam sayılır ve diğer writer'larla serialize edilir.
- Parent/child path'ler çakışır: `FIRST/` ile `FIRST/README.md` aynı batch'e girmez.
- Graph bağımlılığı her zaman paralellik isteğinden üstündür.
- Native worktree yoksa disjoint write scope bile platform davranışı belirsizse manager serialize edebilir.

## Risk ve kalite

`config.json` içindeki high/critical gate politikası, riskli implement türleri için aşağıdaki ilişkileri arar:

- bağımsız bir `review` item'ı → `relations.reviews`
- bir `verify` item'ı → `relations.verifies`
- cross-layer policy açık ise bir `integration` item'ı → `relations.integrates`

Review agent'ı implement eden agent'ın beyanını kanıt saymaz. Result dosyası her acceptance criterion için `passed`, `failed` veya `not_verified` kanıtı taşır. `pass`, bütün acceptance maddeleri `passed` ve hiçbir check `failed` ise kabul edilir.

Eksik/hatalı sonuçta:

1. Orijinal item `failed` olur.
2. Result dosyası ve event geçmişi korunur.
3. Yeni item `relations.revises: ["orijinal-id"]` ile eklenir.
4. Yeni risk seviyesine göre review/verify düğümleri yeniden oluşturulur.

Birden fazla agent aynı probleme alternatif çözüm üretecekse tek item'a birden fazla result yazılmaz. Her aday ayrı, aynı acceptance kriterlerine sahip `candidate-*` item'ı olur. Read-only veya worktree-isolated adaylar paralel çalışır; ardından `kind: comparison` düğümü bütün adaylara `dependsOn` ile bağlanır, kanıtları aynı rubric üzerinde karşılaştırır ve seçimi run `decisions` kaydına yazar. Böylece kaybeden sonuçlar da audit edilebilir kalır.

## Platform seçimi

Adapter dosyaları capability beyanıdır; executable driver değildir. Yönetici seçimi şu sırayla yapar:

1. Aktif platformun gerçekten sunduğu native delegation/tool yüzeyini kontrol et.
2. İş izolasyon/parallelism gerektiriyorsa native subagent kullan.
3. Paralel writer varsa native worktree kullan; yoksa serialize et.
4. Approval gereken eylemi platforma/kullanıcıya bırak.
5. Repo graph'ındaki approval boundary için kullanıcı/platform kararı geldikten sonra `decision` komutuyla actor, gerekçe ve outcome kaydet.
6. Capability yoksa `render` çıktısını ayrı oturuma ver.

Hiçbir adapter harici AI CLI'sını otomatik başlatmaz. Böylece auth, billing, permission, sandbox ve canlı sistem etkileri örtük hale gelmez.

## Context ve map tazeliği

`discover` şu kaynakları gerçek dosyadan tarar:

- `.agents/skills`, `.agent/skills`, `.cursor/skills`, `.claude/skills`, `.codex/skills`
- `.cursor/maps/stack-shared-ai/`
- Bağımlılık haritası varsa `.cursor/maps/stacklit.json` (bu repoda henüz yok)
- `config.json` sourceRoots içindeki ürün belgelerinin kaynak fingerprint'leri
- platform adapter manifestleri

Catalog bir registry değil, snapshot'tır. Yeni skill veya map otomatik görünür. `mapHealth.stale=true` ise manager map'i sadece başlangıç ipucu sayar ve source path'i doğrular. Bu repoda haritalar elle hazırlanan ürün bağlamıdır; generator yoktur. Gerçek belgelerle güncellendikten sonra `map-manifest`, ardından `discover` çalıştırılır.

## Geçmiş, güvenlik ve devam

Her transition `events.jsonl` dosyasına eklenir. Event şu bilgileri taşır: event id, zaman, actor, run/item, önceki/yeni status ve gerekçe. Event silinmez veya yeniden yazılmaz.

Git tesliminde writer subagentlar bağımsız push yapmaz. Dosya değişen her görev sonunda gerekli review/verify/integration kabulünden sonra üst agent yalnız task-owned diff'i `.agent/rules.md` Git Teslim Protokolü ile anlamlı commit'lere ayırır ve pushlar. Yeniden izin istemez; açık kullanıcı istisnasını uygular. Remote hash doğrulanır; force-push yapılmaz.

Mutasyonlar run-level filesystem lock altında yapılır. `revision` alanı ve CLI `--expected-revision` seçeneği, farklı manager oturumlarının eski snapshot ile yazmasını reddeder. Lock zaman aşımı işlem yapılmadan hata verir; manager önce `status` ve event geçmişiyle tekrar uzlaşır.

Run/result dosyalarına secret, token, cookie, authorization header, kişisel veri blob'u veya ham dış sistem mesajı koyma. Path, redacted özet ve güvenli evidence kullan. `historyPolicy.redactKeyFragments` yalnız schema/CLI seviyesinde savunma sağlar; manager ayrıca içerik muhakemesi yapmalıdır.

Devam akışı:

1. `validate <run.json>`
2. `status <run.json>`
3. Son event'leri ve `results/` dosyalarını oku.
4. `active` item gerçekten yaşayan agent'a bağlı değilse önce blocker/failed kararı ver; sessizce kopya iş başlatma.
5. `sync` ile bağımlılığı tamamlanan draft item'ları ready yap.
6. İlk güvenli batch'ten devam et.

## Komut referansı

```text
discover [--out <catalog.json>]
new --id <id> --title <title> --goal <goal> [--out <run-dir>]
validate <run.json>
status <run.json>
sync <run.json> [--actor <name>]
decision <run.json> --id <id> --summary <text> --reason <text> [--item <id> --boundary <name> --outcome approved|denied --provenance user-confirmed|platform-approved] [--actor <name>]
transition <run.json> <item-id> <status> --reason <text> [--actor <name>]
render <run.json> <item-id> --platform codex|cursor|claude-code [--out <prompt.md>]
record <run.json> <result.json> [--actor <name>]
verify-system
```

Komutlar ürün uygulaması veya dış servis başlatmaz. Sadece orkestrasyon artifact'lerini okur/yazar.

## Sistem doğrulaması

```powershell
node --test .orchestrator/test/orchestrator.test.mjs
node .orchestrator/bin/orchestrator.mjs verify-system
python <skill-creator-dir>/scripts/quick_validate.py .agents/skills/orchestrate-project
```

Skill validator yolu Codex kurulumuna göre değişebilir. İlk iki komut repo içidir ve harici paket istemez.
