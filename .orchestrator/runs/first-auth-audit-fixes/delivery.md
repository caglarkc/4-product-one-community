# FIRST backend auth düzeltmeleri

## Yapılan iş

Önceki denetimin P1 ve P2 bulguları backend subagentı tarafından düzeltildi; ayrı reviewer ve ana agent kaynak/diff üzerinden kabul etti.

## Değişen dosyalar

- FIRST/backend/accounts/views.py: start_session yakın kanıtı varsayılan olarak temizler; yalnız şifreli kayıt/giriş password_authenticated=True geçirir. Logout kullanıcı kilidi altında sıralanır.
- FIRST/backend/accounts/account_views.py: tek oturum iptali transaction içinde locked_user kullanır.
- FIRST/backend/projects/views.py: GitHub dış çağrılarından sonra credential kaydından hemen önce locked_user kullanılır.

## Aktif davranışlar

Normal Google girişinin üç yolu ve GitHub girişleri yakın kimlik işareti oluşturmaz, eski işareti taşımaz. Açık Google auth_time doğrulaması ve şifre yeniden doğrulama korunur. Callback son yazımı güncel kullanıcı aktifliği, session expiry/revocation ve security_version kontrolüne bağlıdır. Tekil iptal/logout aynı kullanıcı kilidini paylaşır: iptal önce tamamlanırsa callback reddedilir; callback önce kilidi alırsa bağlantı iptalden önce kurulmuş sayılır.

## Beklenen eklemeler

Canlı dağıtım açık kullanıcı onayını bekliyor. ./send-machine iki kez otomatik onay denetimince yürütülmeden reddedildi. İkinci başvuruda .agent/rules.md:44 ve FIRST/deployment.md kalıcı yetki kanıtı sunuldu; reviewer bu dosya talimatını canlı rebuild/migration/restart için yeterli açık kullanıcı onayı saymadı. Kullanıcıya onay sorusu iletildi. Sunucuda bu görev tarafından mutasyon yapılmadı.

Dağıtım öncesi Google oturumlarına verilmiş eski yakın-kanıt işaretleri geriye dönük temizlenmez; oluşturulmalarından itibaren en fazla 10 dakika geçerli kalabilir. Toplu oturum iptali veya migration eklenmedi.

## Manuel kontrol ve Git

Üç dosya diff'i, tüm start_session çağrıları, yakın kanıt yazımları ve kullanıcı kilidi sırası incelendi; git diff --check geçti. Test, lint/typecheck, yerel build, browser veya gerçek OAuth/eşzamanlılık senaryosu çalıştırılmadı.

Kod commit'i e77671bf6a7ef33dddcb5049dc4d18fcdb5b4c85, origin/main push başarılı ve uzak hash eşleşti. Backend deployment/health henüz çalıştırılmadı.
