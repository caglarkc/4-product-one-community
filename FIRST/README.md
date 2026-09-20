# FIRST — Future Innovators Research & Source Team

Proje ve açık kaynak topluluğu.

Durum: Hesap yönetimi, Google/GitHub girişi, GitHub repo bağlantısı, proje paylaşımı/düzenleme/arşivleme, sınıflandırma ve sayfalı topluluk keşfi uygulanmıştır. İlan ve katılım entegrasyonu [aktif run](../.orchestrator/runs/first-listing-participation/run.json) ile yürütülür. Güncel kabul edilmiş kararlar, açık konular ve askıya alınan mesajlaşma kapsamı [kararlar.md](kararlar.md) dosyasındadır. Ürün kararı ile uygulanmış/test edilmiş davranış ayrı değerlendirilir.

## Amaç

Karar kayıtları: [ürün](kararlar.md), [teknoloji ve yayın](teknik-kararlar.md), [kayıt/giriş](auth-kararlari.md), [öğrenci doğrulaması araştırması](ogrenci-dogrulama-arastirmasi.md).

Başta üniversite öğrencileri olmak üzere, birlikte üretmek isteyen insanların proje keşfetmesini, ekip arkadaşı bulmasını ve mevcut projelere katkı vermesini sağlamak.

## Temel kullanım biçimleri

- Kendi projesini paylaşarak ekip arkadaşı bulmak.
- Bir proje keşfedip ekibine katılmak.
- Mevcut açık kaynak projelerde katkı verilebilecek işleri bulmak ve katkı yapmak.

Üç kullanım biçimi de ürünün kapsamındadır; yalnızca birine odaklanma kararı yoktur.

## Açık ve kapalı repolar

Ana odak açık kaynaktır. Kapalı repolu projeler de ekip arkadaşı veya birlikte üretilecek ortak bulmak için yer alabilir. Kapalı bir reponun koduna erişmek için proje sahibinin erişim izni gerekir.

## Katılım modeli

GitHub katkıcı mantığı temel alınır: Açık bir projeye katkı vermek için önceden ekip üyesi olmak gerekmez. Kişi değişiklik önerisini pull request (PR) olarak sunar; proje sahibi veya yetkili bakımcı inceler ve uygun bulursa birleştirir.

- Katkıcı: Tek bir hata düzeltmesi, özellik veya dokümantasyon katkısı yapabilir; sürekli sorumluluk üstlenmesi gerekmez.
- Ekip üyesi: Projede devamlı çalışır ve sorumluluk üstlenir. Katkıcılık zamanla ekip üyeliğine dönüşebilir.

## Freelance ürünüyle sınır

Ayrımı reponun açık veya kapalı olması değil, çalışma ilişkisi belirler. Birlikte üretmek için ekip veya ortak aramak topluluk kapsamındadır. Belirli bir işi ücret karşılığında yaptırmak freelance kapsamındadır. Açık kaynak projelerdeki ücretli işler de freelance tarafıyla bağlantılı olabilir.

## Konuşulan özellik önerileri

Aşağıdakiler ürün yönünü destekleyen önerilerdir; kesin özellik listesi veya teknik uygulama kararı değildir:

- Projenin amacı, aşaması, ekibi, ihtiyaç duyduğu beceriler ve repo görünürlüğünü içeren proje sayfası.
- Hem projeleri hem de projelerin katkı bekleyen görevlerini keşfetme.
- Yeni başlayanlar için küçük, açıkça tanımlanmış görevler.
- Profillerde yapılan ve kabul edilen katkıların görünmesi.
- Projelerin aktifliğinin ve güncel ekip ihtiyaçlarının görünmesi.
- Kodun GitHub’da kalması; platformun keşif, ekip bulma ve katkıya başlama deneyimine odaklanması.

## Normal auth uygulama durumu

E-posta/şifre kaydı ve girişi, beni hatırla, oturum sorgulama/çıkış, profil/telefon güncelleme, parola kurtarma/değiştirme, yeniden doğrulama, e-posta doğrulama/değiştirme ve oturum yönetimi backend ile webde uygulandı. `/hesap` gerçek API'ye bağlı profil ekranıdır. İlk auth tesliminden sonra Google/GitHub OAuth, repo bağlantısı ve proje paylaşımı eklendi; ana sayfa gerçek sayfalı topluluk akışıdır. Öğrenci doğrulaması hâlâ sonraki kapsamdadır.

[Backend](backend/README.md), [web](frontend/README.md), [API sözleşmesi](contracts/auth-api.md) ve [run checklist](../.orchestrator/runs/first-auth/checklist.md) uygulama, test ve bağımsız kontrol kanıtlarını içerir. İzole backend/frontend testleri ile lint/typecheck/build çalıştırıldı. Gerçek PostgreSQL/Redis/SMTP, ingress/proxy/HTTPS-cookie, tarayıcı E2E ve deploy **not_verified**; kod kontrolleri canlı ortam doğrulaması değildir.
