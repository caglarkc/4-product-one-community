# A hazırlık kontrolü
Görev/dosyalar: a-preparation; AGENTS, belirtilen skill ve FIRST ürün/auth/teknoloji belgeleri, auth-api.md, run.json, technical-decisions.md, checklist.md. Diğer ürün belgeleri yüklenmedi.
Komutlar: pwd; git status --short; git branch --show-current; git remote -v; rg --files FIRST .orchestrator; cat kaynak belgeler; node .orchestrator/bin/orchestrator.mjs discover/status/validate.
Sonuç: ilk Git temiz, main/origin doğrulandı; backend yalnız sağlık iskeleti, frontend yok. Sözleşme endpoint/veri/test alanları tamamlandı. Eski sonuç/eventler korundu. Dosya sahipliği graph içinde; ana agent sözleşme/run/Git sahibi, aşama writer yalnız backend veya frontend, review/verify read-only.
Başarısız denemeler: codex.md yok, codex.json okundu; ilk graph validate eski failed node review ilişkisi hatası; ikinci validate ancestor hatası; legacy review düğümleriyle son validate geçti. Kanıt: events.jsonl ve technical-decisions.md.
Yapılmayanlar: gerçek servis ve çalışma zamanı kontrolleri kullanıcı sınırı gereği not_verified. Aşama A yalnız hazırlık; kod testleri henüz yok.
