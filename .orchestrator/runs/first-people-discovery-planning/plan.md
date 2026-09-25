> 25 Eylül 2026: Bu belge tarihsel planlamadır. Uygulama ve yayın first-community-discovery/delivery.md ile teslim edilmiştir; aşağıdaki başlangıç durumu güncel eksik olarak okunmamalıdır.

# FIRST — Profil ve keşif geliştirme taslağı

Durum: Kullanıcı yanıtlarıyla uygulama planı hazır. Uygulama başlamadı.

## Kapsam
- Herkese açık kullanıcı profili; tanıtım, beceri ve ilgi alanları; sahibin profiline karttan geçiş.
- Kişi listesi, metin araması, beceri/ilgi filtreleri ve sayfalama.
- Davete açıklık tercihi ve profilden mevcut ilan seçerek katılım daveti.
- Proje metin araması; teknoloji ve aranan beceri alanları/filtreleri.
- Kullanıcıya özel kaydedilen projeler.
- İlan/profil şikâyeti oluşturma, backend doğrulaması ve veritabanına kayıt. Yönetim ekranı ve yaptırımlar sonraya bırakıldı.

Kapsam dışında: katkıcı listeleri/istatistik, ekip sayfaları, private repo dosya vitrini. Önceki ertelemeler korunur: sohbet, öğrenci doğrulaması, sertifika vitrini ve ilan dışı repo vitrini.

## Mevcut kaynak bulguları
- accounts/models.py yalnız hesap profilini içeriyor; topluluk profili/beceri/ilgi/davet tercihi henüz yok.
- projects/views.py keşfi kategori, alt kategori, aşama, ihtiyaç ve katılım yöntemiyle filtreliyor; metin araması yok.
- projects/participation_views.py InvitationView mevcut doğrulanmış hesap/GitHub koşullarını uyguluyor. Yeni tercih hem bu uçta hem yeni profil girişinde uygulanmalı.
- Proje kartında owner_username var; kişi profili route ve bağlantısı yok.
- Kaydetme ve şikâyet modeli/API/ekranı bulunmuyor. Mevcut erişim denetimleri tekrar kullanılmalı.
- Ürün haritaları eski; gerçek kaynaklar esas alındı.

## Kesinleşen kararlar — kullanıcı yanıtı
- Profil ziyaretçilere açık; kişi aramasında görünme kullanıcı tarafından kapatılabilir. Önerilen görünen ad/kullanıcı adı/tanıtım/beceri/ilgi/GitHub/web alanları uygun bulundu. E-posta, telefon ve doğum tarihi gösterilmez.
- Davet alma yeni ve mevcut kullanıcılarda varsayılan açık. Kullanıcı kapatınca tüm yeni katılım davetleri engellenir; mevcut davetler ve kendi başvuruları etkilenmez.
- Şikâyet için yalnız oluşturma/kayıt yapılır. Yönetim paneli, inceleme/yaptırım iş akışı ve karar bildirimleri sonraya bırakıldı.

## Uygulama ayrıntıları
1. Avatar kaynağı önerisi: sağlayıcı resmi veya baş harf; dosya yükleme bu kapsamda yok.
2. Davet tercihi kesinleşti: varsayılan açık, kapalıysa API düzeyinde yeni davet engellenir.
3. Kesin karar: beceri/teknoloji ortak çoklu seçim kataloğu; serbest etiket yok. İlgi alanları mevcut proje kategorilerinden seçilir.
4. Şikâyet kaydı saklama/silme yaklaşımı uygulama sözleşmesinde netleştirilecek; bu tur otomatik temizlik/yaptırım veya inceleme ekranı yok.
5. Kesin karar: kişi keşfi yalnız GitHub bağlı, aktif ve keşfe açık kullanıcıları listeler; bağlantı kaldırılınca keşiften çıkar. Davette mevcut doğrulama koşulları korunur.

## Teknik yaklaşım ve korunacak sınırlar
- Profilde e-posta, telefon, doğum tarihi ve cinsiyet yayımlanmaz.
- Özel liste/görünürlükteki projeler profil ve arama üzerinden açığa çıkmaz.
- Kaydetme erişim vermez. Erişim kaybolduğunda kart ayrıntıları gizlenir, kullanıcı kendi kaydını kaldırabilir.
- Etiketler ortak katalogdan çoklu seçilir; teknoloji, beceri ve ilgi ayrı alanlardır. İlk aşamada serbest etiket üretimi yok.
- Proje metin araması başlık/açıklama; kişi araması kullanıcı adı/görünen ad; Türkçe harf ve büyük/küçük harf davranışı açıkça tanımlanır.
- Kişi için görünen ad ve kullanıcı adı; kısa tanıtım; isteğe bağlı GitHub/web bağlantısı. Avatar için sağlayıcı resmi veya baş harf; ayrı dosya yükleme başlangıç kapsamına eklenmez.
- Şikâyet gerekçeleri spam, taciz, uygunsuz içerik, yanıltıcı bilgi ve diğer; açıklama ve yinelenen açık şikâyet sınırı.
- Şikâyet sayısı otomatik ceza oluşturmaz; şikâyetçi kimliği karşı tarafa gösterilmez. Yönetici işlemleri bu kapsamda yok.

## Uygulama sırası ve sahiplik
1. Kararları kesinleştir; API/veri alanı, görünürlük ve şikâyet kayıt sözleşmesi hazırla.
2. Backend: profil/etiket/migration → kişi arama → davet tercihi → proje arama/kaydetme → şikâyet oluşturma/kayıt. accounts ve projects değişiklikleri ortak yazarlıkla sıralı yürütülür.
3. Frontend: profil düzenleme ve public profil → kişi keşfi ve profilden davet → proje filtreleri/kaydetme → şikâyet formları ve kayıt sonucu. Mevcut FIRST token ve ortak UI kullanılır.
4. Bağımsız kaynak incelemesi ve kabul maddelerinin doğrulanması → katman entegrasyonu.
5. Kullanıcı test aşamasını yetkilendirirse: görünürlük, davet tercihi, arama, kaydetme, şikâyet erişim sınırları ve eski akışlar için hedefli testler; ardından commit/push, standart backend dağıtımı, Vercel sonucu. Varsayılan olarak test/browser çalıştırılmaz.

## Kabul ölçütleri
- Karttaki sahip adı doğru profile gider; kişisel hesap verileri public yanıta girmez.
- Kişi keşfi görünürlük/filtre/sayfalama kurallarını uygular; kapatılan profil aramada görünmez.
- Davet için hem ilan sahipliği hem alıcının tercih/uygunluk koşulları backend’de doğrulanır; gönderim tekilleştirilir.
- Profil proje listesi ve kaydedilenler mevcut proje erişimini aşamaz.
- Proje araması var olan filtrelerle birlikte çalışır; kategori ve beceri alanları karışmaz.
- Kaydedilenler yalnız sahibine görünür; ekle/kaldır tekrarlarında çoğalmaz.
- Şikâyetler başka kullanıcılara açılmaz; oluşturma başarılıysa kayıt numarası/sonuç döner. İnceleme ekranı yok.
- Şikâyet oluşturmak ilanı/hesabı otomatik kapatmaz; GitHub repo/PR/Issue veya erişim üzerinde işlem yapmaz.

## Kontrol
Bu tur yalnız kaynak okuma ve plan hazırlığıdır. Ürün kodu, veri veya canlı davranış değiştirilmedi; test/tarayıcı kontrolü yapılmadı.

## Bağımlılık sırası
Kararlar → API/veri sözleşmesi → backend/migration → frontend → bağımsız kaynak review → kaynak verify → integration → teslim. Uygulama run'ında API/veri/izin düğümlerine bağımsız review ve verify ilişkileri zorunludur. Bu planlama run'ı uygulama yetkisi veya tamamlanma kanıtı değildir.

## Bağımsız plan incelemesi
Read-only discovery_plan_review incelemesi: profil gizliliği, davet tercihi, ortak etiketler, kaydetmenin erişim vermemesi ve şikâyet kapsamı kontrol edildi. Eski auth kararındaki private yalnız davet ifadesi güncel ilan kararını geçersiz kılamaz. Kullanıcı yanıtlarıyla yönetim/yaptırım kapsamı çıkarıldı.
