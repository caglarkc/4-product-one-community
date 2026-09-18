# FIRST — ortak tasarım dili

18 Eylül 2026: Kullanıcı konseptin **renk tonlarını ve genel tema hissini** onayladı. Görseldeki yerleşimi, proje kartlarını veya örnek içerikleri onaylamadı. Bu belge FIRST'ün mevcut ve sonraki sayfalarının görsel ortak noktasıdır; yeni ürün özelliği veya ekran kapsamı oluşturmaz.

## Görsel yön

“Ortak Atölye”: sıcak, sakin, anlaşılır ve üretmeye davet eden bir arayüz. Kırık beyaz ana zemin, koyu mürekkep metin, orman yeşili aksiyonlar, adaçayı destek yüzeyleri ve küçük mercan vurgular. Büyük pazarlama hero'ları, gösterişli gradient'ler, ağır gölgeler veya dekorasyonla dolu ekranlar gerekmez. Sayfa düzenini gerçek kullanıcı işi belirler.

## Merkezi tanımlar

Uygulanabilir değerlerin tek kaynağı `frontend/src/app/tokens.css`; tekrar kullanılan React öğelerinin kaynağı `frontend/src/components/ui/` dizinidir. `globals.css` bu token'ları tüketir ve ortak kabuk/düzen stillerini tanımlar. Sayfalar ortak öğeleri birleştirir; aynı butonu, alanı veya durum kutusunu tekrar biçimlendirmez.

| Rol | Başlangıç değeri | Kullanım |
|---|---|---|
| Ana zemin | `#F7F6F0` | Sayfa arka planı |
| Yüzey | `#FFFFFF` | Form ve içerik yüzeyleri |
| Mürekkep | `#202A27` | Başlık ve ana metin |
| İkincil metin | `#57645D` | Yardım metni; okunaklı kontrast |
| Ana aksiyon | `#225447` | Birincil buton, aktif öğe, bağlantı |
| Ana aksiyon hover | `#193E34` | Hover/pressed |
| Adaçayı yüzey | `#DCE8DE` | Bilgilendirme ve yardımcı yüzey |
| Mercan vurgu | `#CB7257` | Küçük dekoratif vurgu; beyaz küçük yazıyla kullanma |
| Koyu mercan | `#94432E` | Açık zeminde uyarı/vurgu yazısı |
| Kenarlık | `#D4DAD1` | Yüzey ayrımı; kontrol ve odak için daha belirgin token gerekebilir |

Bu değerler onaylı yönün başlangıç paletidir. Hata, başarı, uyarı, kontrol kenarlığı ve disabled gibi semantik renkleri aynı merkezi dosyada tanımla. Normal metin için en az 4.5:1, büyük metin ile gerekli UI sınırları/odak için en az 3:1 kontrast hedefle. Erişilebilirlik için tonu koyulaştırmak temayı değiştirmek sayılmaz. Renk tek durum göstergesi olmasın.

- Tipografi: Türkçe karakterleri destekleyen sistem sans ailesi; dış font indirmesine bağımlılık yok. Başlık, gövde, etiket ve yardımcı yazı boyutları ortak token'lardan gelir. Gövde yaklaşık 16px ve rahat satır yüksekliğindedir.
- Boşluk: 4/8 tabanlı tutarlı ölçek; form grupları arasında rahat nefes alanı. Gereksiz büyük boş paneller oluşturma.
- Köşe: yüzeyler yaklaşık 12px, alan ve butonlar yaklaşık 8px. Değerleri merkezi değişkenlerden kullan.
- Etkileşim: butonlar ve alanlar en az 44px kullanım yüksekliğini hedefler. Belirgin klavye odağı, hover, disabled ve bekleme durumları ortaktır; hareket varsa `prefers-reduced-motion` dikkate alınır.

## Ortak bileşen sözleşmesi

- `Button`: primary/secondary/quiet/danger gibi ihtiyaç duyulan varyantlar ve loading/disabled durumları tek uygulamada. Varsayılan `type="button"`; form gönderiminde `type="submit"` açık belirtilir.
- Aksiyon bağlantısı: aynı görsel dili kullanır ancak gerçek bağlantı semantiğini korur. Sayfa geçişi buton taklidiyle yapılmaz.
- Form öğeleri: ortak field/label/help/error, input/select/checkbox. Native `name`, `type`, `required`, `autoComplete`, `aria-*`, `disabled` ve form gönderim davranışları korunur. Birden fazla formdaki ID'ler çakışmaz.
- Durum kutusu ve yüzey: hata, bilgi, başarı, yüklenme için anlamlı görünüm; `alert` veya `status` semantiği gerektiren yerlerde korunur. Her kutuyu canlı bölge yapma.
- Sayfa kabuğu ve başlık: gezinme, içerik genişliği ve başlık hiyerarşisi ortak yaklaşımı izler. Form sayfaları dar/odaklı, hesap sayfası daha geniş olabilir; bütün sayfaları aynı yerleşime zorlama.

Bir ortak öğeyi değiştirmek için sayfaları tek tek düzenlemek gerekmemelidir. Sayfaya özgü CSS yalnız gerçek düzen ihtiyacı için eklenir; hex renk, kopya kontrol stili veya ayrı tema yazılmaz. Yeni bağımlılık veya kapsamlı component framework'ü bu işin gereği değildir.

## Mevcut ekranlara uygulama

Ana sayfa mevcut oturum özeti ve gerçek gezinmeyle sınırlı kalır. Giriş, kayıt, şifremi unuttum, şifre sıfırlama, e-posta doğrulama ve hesap yönetimi aynı görsel dili kullanır. Profil, telefon, yeniden doğrulama, parola/e-posta değişimi, e-posta hatırlatması ve oturum kapatma işlevleri korunur. Henüz uygulanmamış keşif/ekip/kişi sayfaları, sosyal giriş butonları ve mock proje kartları eklenmez.

## Doğrulama

Mevcut işlev testleri, lint, typecheck ve build korunur. Görsel kontrolde masaüstü ve dar ekran; uzun kayıt/hesap formları; hata, başarı, loading/disabled ve klavye odağı incelenir. Backend'i veya kullanıcı hesaplarını değiştirmeden görünüm için kullanılan test verisi ürün koduna girmez. Kontrol edilmemiş canlı akışları doğrulanmış sayma.
