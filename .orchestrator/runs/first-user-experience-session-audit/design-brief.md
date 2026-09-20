# FIRST kullanıcı arayüzü düzeni

Kapsam: mevcut FIRST ekranları. Yeni keşif, ekip, mesajlaşma veya sahte veri eklenmez.

## Oturum ve gezinme

- Ziyaretçi: FIRST ana sayfası, Giriş yap ve Hesap oluştur.
- Üye: ana sayfa, Projelerim, Hesabım ve çıkış işlemi. Giriş/kayıt formları yerine üye ana sayfası.
- Kontrol sürerken: nötr yüklenme durumu; özel bağlantı veya anonim aksiyonlar erken gösterilmez.
- Ağ hatasında: yeniden deneme; kullanıcı çıkış yapmış varsayılmaz.
- Hesap ve proje yönetimi ekranları üyelik kontrolüne bağlıdır. Public proje detayı açık kalır. Kurtarma, doğrulama ve OAuth callback akışları genel yönlendirme kurallarından ayrı tutulur.
- Aynı sekme ve diğer sekmedeki giriş/çıkış, oturum iptali ve kullanıcı güncellemeleri ortak oturum durumuna yansır. Geç kalan cevaplar yeni oturumun kimliğini ezemez.

## Sayfa kurgusu

- Ana sayfa: ziyaretçiye kısa topluluk tanıtımı ve giriş/kayıt; üyeye karşılama, gerçek proje oluşturma/yönetme ve hesap bağlantıları.
- Giriş/kayıt: odaklı form, sosyal sağlayıcılar ve e-posta yöntemi arasında açık ayrım; hata ve bekleme durumları korunur.
- Hesap: profil, bağlı hesaplar, güvenlik ve açık oturumlar ayrı anlamlı bölümler. Bağlantı kaldırma/hesap silme kullanıcı dilinde anlatılır, mevcut yeniden doğrulama ve silme onayları korunur.
- Projeler: tutarlı başlık ve geri bağlantıları, rahat yüzey boşlukları, boş durum, yüklenme ve yeniden deneme. Gizli repo özeti onayı ve erişim koşulları korunur.
- Görsel dil: mevcut kırık beyaz/orman yeşili tema, semantik token ve ortak UI bileşenleri, dar ekranda doğal akış, görünür klavye odağı.

## Denetim ve teslim sınırı

Backend ayrı subagent tarafından salt okunur denetlenir. FIRST Redis Bearer oturumu, GitHub App access/refresh tokenlarından ayrı değerlendirilir; bu görev JWT mimarisine geçiş kararı değildir. İnceleme süre, iptal, yetki, CSRF, OAuth geçişleri ve sağlayıcı token yenilemesini kapsar.

Uygulama sonrası bağımsız kaynak/diff incelemesi ve yönetici kabul kontrolü yapılır. Test, lint, typecheck, build ve browser çalıştırılmaz; canlı davranış ve görsel sonuç doğrulanmış sayılmaz.
