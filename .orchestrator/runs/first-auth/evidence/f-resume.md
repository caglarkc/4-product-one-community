# F başlangıç / resume kontrolü
Görev/dosyalar: f-backend; FIRST/backend, auth-api.md, technical-decisions.md; run/events/checklist.
Komutlar: git status --short; git log -4 --oneline; orchestrator validate/status; tail events; gerçek backend security/views ve sözleşme okuma.
Sonuç: çalışma ağacı temiz, HEAD97cf377; E independent review/verify/integration done. Eski failed denemeler değiştirilmedi. Kullanıcı bekleme talimatını kaldırdı. f-backend blocked→ready→active; backend_writer yalnız FIRST/backend üzerinde dispatch edildi. G yazımı başlamadı.
Kontrol odağı: reset token30dk/tek kullanım/tüm session iptali; reauth600s/shared proof limit; verify24saat/resend60s5saatlik değil 5/saat; eski adres korunarak yeni adres sahipliği; profil whitelist/phonefalse; cross-user session reddi. Gerçek komut sonuçları writer ve bağımsız kapı evidence kayıtlarında tutulacak.
Yapılmayanlar: gerçek servis/runtime/deploy/E2E kullanıcı sınırı nedeniyle not_verified. Bu resume kanıtı F implementasyonu geçti anlamına gelmez.
