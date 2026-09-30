# STEP sağlayıcı adaptör sözleşmeleri

Ödeme önerisi iyzico Marketplace, on-demand withdrawal yeteneği ayrıca sözleşme teyidine bağlı. Backend `Iyzico` ödeme transportu ve `PayoutGateway` banka kabiliyet arayüzü ayrıdır. Default local geliştirme fixture `simulator` ile gerçek `iyzico_sandbox` / `iyzico_live` kayıtları ayrı tutulur; simulator gerçek provider kanıtı değildir.

| Operasyon | iyzico method/path | Doğrulama |
|---|---|---|
| personal submerchant | POST /onboarding/submerchant | PERSONAL, gerçek alıcı ownname IBAN/TCKN/phone; raw identity logs/response yok |
| checkout init | POST /payment/iyzipos/checkoutform/initialize/auth/ecom | TRY, amount server target, VIRTUAL item; token success funded değildir |
| checkout retrieve | POST /payment/iyzipos/checkoutform/auth/ecom/detail | paymentStatus/status/fraudStatus, amount/currency, conversation/merchant payment target, itemtxid doğrula |
| seller price update | PUT /payment/item | net90% ve unused funds için stored target doğrula |
| approval/disapproval | POST /payment/iyzipos/item/approve veya /disapprove | bank settlement ayrı; başlatma paid demek değil |
| refund/cancel | POST /payment/refund veya /payment/cancel | refund item-level/price, cancel same-day wholepayment; request ve confirmed ayrı |
| mass payout | POST /v1/mass/payout/init, /auth, /retrieve; GET /balance | init externalId tekil, peritem result; Marketplace settlement + ikinci payout yok |

Resmî kaynaklar: [Marketplace](https://docs.iyzico.com/urunler/pazaryeri), [submerchant](https://docs.iyzico.com/urunler/pazaryeri/pazaryeri-entegrasyonu/alt-uye-olusturma), [Checkout init](https://docs.iyzico.com/odeme-metotlari/odeme-formu/cf-entegrasyonu/cf-baslatma), [retrieve](https://docs.iyzico.com/odeme-metotlari/odeme-formu/cf-entegrasyonu/cf-sorgulama), [item update](https://docs.iyzico.com/urunler/pazaryeri/pazaryeri-entegrasyonu/alt-uye-olusturma/alt-uye-urun-guncelleme), [approve](https://docs.iyzico.com/urunler/pazaryeri/pazaryeri-entegrasyonu/onay), [refund](https://docs.iyzico.com/en/advanced/refund-and-cancel), [Mass Payout](https://docs.iyzico.com/en/products/mass-payout), [idempotency](https://docs.iyzico.com/en/getting-started/preliminaries/idempotency).

Provider HTTP auth iyzico resmî IYZWSv2 HMAC protokolü, JSON serialization ve authorization/header redaction ile yapılır. `conversationId` idempotency garantisi değildir. Intent DB transaction'da hazırlanır, dış network locks dışında yürür; timeout pending/unknown + reconciliation. Blind init/refund/approve retry yok. Callback provider token'a güvenmez: storedtoken/paymentbinding ve server retrieve kanıtı.

Mass Payout canlı capability default false; Marketplace seller bank transferi ile aynı kazanç ledgerı iki kez paid olamaz. Kısmi hakediş/unused refund/rollover ve withdraw financing/provider underwriting koşulları belge/hesap yetkisi ile ayrıca doğrulanır. Yapılandırma eksikse fail-closed; mevcut %10 ürün komisyonu dışında vergi/provider fee fiyatı eklenmez.

Telefon: [Netgsm resmi docs](https://www.netgsm.com.tr/dokuman/) OTP HTTP gateway; send sonucu phoneverified değil. Random code hash+expires+attempt counter; doğru code kullanıcı submit ile status. Live identity/company/authorized verification yetkili dış kontrol reference case review; KPS hizmeti erişimi olmadan public eski SOAP varsayımı yok. [NVİ KPS](https://www.nvi.gov.tr/kps). Provider veya operator kanıtı olmadan verified bayrağı yok; ek studentdocument eligibility şartı yok.

Platform şirket/KYC/iş modeli kabulü: [iyzico başvuru](https://www.iyzico.com/destek/yardim-merkezi/entegrasyon/hazir-altyapilar). Bu source entegrasyonu sağlayıcı hesabı veya canlı onay alınmış iddiası değildir.


## Kaynak çekim operasyonu ve test fixture sınırı

Yerel fixture alıcı kaydı gerçek kimlik veya banka doğrulaması değildir. Payout ledger test mode/provider altında ayrı kalır; `bank_transfer_proven=false` sonucu webde açıkça gösterilir. Operator yalnız açık success/failure seçimiyle test rezervini sonuçlandırır.

Gerçek Marketplace approval, seller settlement takvimini etkiler; aynı alacak için ayrıca MassPayout başlatılmaz. On-demand bank operation sağlayıcı sözleşmesi henüz kanıtlanmadığından kaynak bunu unavailable/blocked olarak bildirir. Bu bir transfer tamamlandı cevabı değildir. Gönderilmemiş talep izinli operator gerekçesiyle reject edilerek rezervi geri verebilir. Belirsiz aktarımda bank proof olmadan rezerv kaldırılmaz. Kaynak-bank settlement kayıtları payment-bound ve tekildir; operatör referansı gerçek retrieval yerine geçmez. Canlıya hazırlık bu missing_operation ve sağlayıcı underwriting/KYC/rollover şartlarını açık iş olarak tutar.


## Belirsiz işlemin sorgulanması

Token kaydedilmiş hosted checkout kendi token/conversation ile; initialize sonucu token kaydetmeden kesilmişse POST `/payment/detail` kayıtlı `paymentConversationId` ile sorgulanır. Terminal başarısızlık olmadan yeni initialize yapılmaz. Alt üye için POST `/onboarding/submerchant/detail` aynı `subMerchantExternalId` üzerinden kayıtlı alıcı ve banka bilgilerini doğrular. Operatör gerekçeli ve permission-scoped uzlaştırma dışında raw provider payload erişimi yoktur.

Marketplace item status/net kanıtı GET `/v2/reporting/payment/details?paymentId=...` üzerinden kayıtlı payment/deneme/TRY/item'e bağlanır. GET signing/transport gövdesi boştur. Refund yanıtta conversation/item/price/currency ile kanıtlanır; raporun belirsiz sayısal refundStatus değeri uydurulmuş terminal anlamla kabul edilmez. On-demand banka kabiliyeti resmî sözleşmeyle tamamlanmadan tahmini bankTransferStatus alanı veya manual paid flag başarı yolu değildir.
