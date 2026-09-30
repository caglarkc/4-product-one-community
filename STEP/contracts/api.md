# STEP v1 — ortak API sözleşmesi

Bu sözleşme backend, web ve masaüstü tüketicilerinin tek kaynağıdır. `/api/v1/` öneki, JSON ve UTF-8; kimlikler UUID string, paralar iki basamaklı ondalık string, zamanlar timezone-aware ISO 8601. Liste cevapları `{results: [...], count: n, next: url|null}`; nesne cevapları doğrudan nesnedir. Hatalar `{code, detail, fields?}` ve uygun HTTP durumudur. Sayfalama `page`/`page_size`, üst teknik sayfa boyutu 100; bu iş ilanındaki işe alım sayısı sınırı değildir. Mutasyonlar actor+operation kapsamında `Idempotency-Key` UUID ve request digest kullanır; başka payload ile tekrar 409. Özel medya public URL değildir; aynı auth/visibility kontrollerinden geçen dosya endpoint'i kullanılır.

Web: Django HttpOnly session cookie, GET `auth/csrf/` ile `{csrf_token}`; mutasyonlarda `X-CSRFToken`, credentials include. Güvenilir frontend origin/CORS/CSRF `.env` ile belirtilir. Desktop: `auth/device-login/` geçici ham Bearer token döndürür, DB yalnız hash tutar; süresi ve iptali vardır. Password değişimi/sıfırlama bütün oturumları iptal eder. Desktop token webde localStorage'a taşınmaz. Device allowlist: auth/logout, tracker/config/contracts/sessions/blocks ve yalnız kendi screenshots image/review-ready/publish/privacy yolları; diğer market/credit/money/admin mutation yolları device token için kapalıdır. Login/register/reset rate-limit uygulanır; reset bilinmeyen emaili ifşa etmez.

## Hesap ve keşif

| Yöntem/yol | İstek | Cevap/izin |
|---|---|---|
| GET config/ | — | mode, payment_provider, payment_ready, verification_required, credit_policy (nullable rakamlar), tracker_policy (nullable idle/preview), categories; secret yok |
| GET auth/csrf/ | — | csrf_token |
| POST auth/register/ | email,password,display_name,roles[] | user; session. Öğrenci/employer rollerini aynı hesap kullanabilir |
| POST auth/login/ | email,password | user; session |
| POST auth/logout/ | — | 204; session/device token iptal |
| GET auth/me/ | — | id,email,display_name,roles,is_staff,profile,verification,preferences |
| POST auth/password-reset/ | email | genel teslim bildirimi; SMTP yoksa sunucu yanlış başarı vermeden genel operasyon hatası |
| POST auth/password-reset-confirm/ | token,password | 204 |
| POST auth/device-login/ | email,password,device_name | token,expires_at,user; rate limit |
| GET/PATCH profile/ | university,department,bio,skills[],hourly_rate,photo?,portfolio_links[] ({title,url,kind}) | kendi profil; public profil email/iletişim taşımaz |
| GET profiles/ ; GET profiles/{id}/ | q?,skill? | genel öğrenci profilleri |
| POST verification/student/ | student_email,birth_date,education_level | üniversite email doğrulama challenge gönderimi; domain whitelisted |
| POST verification/student-confirm/ | token | verified_until; yılda bir yenileme |
| POST verification/student-status/ | status:graduated\|access_lost | yeni başvuruyu kapatır, mevcut işler sürer |
| POST verification/phone/start/ | phone | Netgsm OTP gateway; testte gate ertelenir; gönderim verified demek değildir |
| POST verification/phone/confirm/ | code | süreli hash/attempt limit ile telefon teyidi |
| POST payment-profile/ | legal_name,phone,identity_number,address,iban | provider PERSONAL onboarding; raw identity_number response/audit/DB log yok; key/yetki yoksa unavailable |
| POST verification/employer/ | kind:individual\|company, phone, legal_name, company_name?, company_registration? | kontrollü doğrulama başvurusu; canlıda harici kanıt olmadan verified olmaz |
| PATCH preferences/ | in_app,email | tercih |
| GET notifications/ ; POST notifications/{id}/read/ | — | yalnız alıcı |

## Pazar ve takım

Job: id,owner,owner_name,title,description,category,skills[],work_type:fixed\|hourly,budget,expected_duration,deadline?,status:draft\|open\|cancelled\|removed\|closed,created_at,boosted_until?,attachments[]. Genel dosya erişimi açılmaz.
Application: id,job,student,team?,cover_letter,price,duration,sample_url?,status:submitted\|withdrawn\|rejected\|selected,conversation,created_at,boosted_until?. Öğrenci kendi teklifini; işveren kendi ilanının tekliflerini görür. Invitation: id,job,student? veya team?,status,conversation.
Team: id,name,description,leader,members[] ({user,display_name,status}),wallet_id. Üyelik davet/kabul; kendiliğinden başka kullanıcı eklenmez.

| Yöntem/yol | İstek | İzin/davranış |
|---|---|---|
| GET jobs/ ; GET jobs/{id}/ | q?,category?,work_type?,mine? | genel open keşif; mine kendi tüm ilanları |
| POST jobs/ ; PATCH jobs/{id}/ | Job alanları; publish? | sahibi, fiyat/başlık zorunlu; yayın kredi ve canlı employer gate |
| POST jobs/{id}/publish/ | — | sahibi; sabit kredi politikası yapılandırılmış olmalı |
| POST jobs/{id}/cancel/ | reason | owner; anlaşma olmayan ilan için kabul edilmiş kredi iadeleri; aktif sözleşme ayrı iptal |
| POST jobs/{id}/report/ | reason | girişli; moderasyon kuyruğu |
| GET/POST jobs/{id}/applications/ | cover_letter,price,duration,sample_url?,team? | create öğrenci veya team leader; davet varsa kredi kesilmez |
| GET applications/ ; PATCH applications/{id}/ | mine list; düzenleme teklif alanları | seçim öncesi kendi/leader |
| POST applications/{id}/withdraw/ | — | seçim öncesi kendi/leader; kredi iade yok |
| POST applications/{id}/reject/ | — | job owner; kredi iade yok |
| POST jobs/{id}/invitations/ | student veya team | job owner; mesaj ilişkisi açılır |
| GET invitations/ ; POST invitations/{id}/decline/ | — | yalnız davet tarafı/owner |
| GET/POST teams/ ; GET/PATCH teams/{id}/ | name,description | üyelikleri yetkili; genel tanıtım ayrıca public olabilir |
| POST teams/{id}/invite/ | email | leader; kabul bekleyen üyelik |
| POST teams/{id}/membership/ | action:accept\|decline\|leave | ilgili üye; aktif sözleşme haklarını sessizce değiştirmez |
| POST teams/{id}/leader-change/ | new_leader,payee,reason,contract_ids[] | leader; mevcut aktif işlerde employer+admin onayını bekler |
| POST leader-changes/{id}/approve/ | — | ilgili employer ve admin ayrı onay; payee kimliği ayrıca teyit edilir |

## Sözleşme ve iş alanı

Contract: id,job,application,employer,freelancer,team?,payee,status:pending\|active\|completed\|cancelled,scope,work_type,rate,weekly_limit,expected_duration,revision_terms,tracker_required,members[] ({user,hourly_rate}),milestones[],accepted_by[],conversation. Takımda temsilci leader, ödeme alıcısı ayrı kayıttır. Milestone: id,title,amount,status:unfunded\|funded\|in_progress\|submitted\|revision\|disputed\|released\|refunded,submission?,submitted_at?,review_due_at?. Week: id,contract,starts_at,ends_at,status:unfunded\|funded\|review\|disputed\|released,limit_hours,reserved_amount,worked_seconds,gross,net,review_due_at.

| Yöntem/yol | İstek | İzin/davranış |
|---|---|---|
| GET/POST contracts/ ; GET contracts/{id}/ | create: application,scope,expected_duration,revision_terms,weekly_limit?,members[],milestones[] ({title,amount}) | create job owner, taraflar/işe dahil üye list/detail |
| POST contracts/{id}/accept/ | — | employer+freelancer veya leader; canlı tüm çalışanlar uygun |
| POST contracts/{id}/changes/ | scope?,rate?,weekly_limit?,expected_duration?,revision_terms?,milestones?,members? | karşılıklı onaylı revizyon önerisi; aktif işlem geçmişi değişmez |
| POST contract-changes/{id}/accept/ | — | karşı taraf; iki taraf kabul edilmeden aktive olmaz |
| POST contracts/{id}/cancel/ | reason | ilgili taraf; approved ödenir, unstarted fon refund, worked/unapproved dispute |
| POST contracts/{id}/complete/ | — | aktif, açık fon/iş/itiraz kalmamış; karşılıklı sonuç |
| POST milestones/{id}/start/ | — | worker; ön fon kontrolü |
| POST milestones/{id}/submit/ | text,attachment_ids[] | worker; funded; yeniden teslim 14 gün yeniler |
| POST milestones/{id}/review/ | decision:approve\|revision\|dispute,reason? | employer; 14 gün sessizlik tick release, itiraz hold |
| GET/POST contracts/{id}/weeks/ | create: starts_at? (hafta),remainder_choice:refund\|rollover | employer; farklı rate için ortak limitin güvenli reserve hesabı |
| POST weeks/{id}/close/ | — | employer veya dönem sonu tick; 5 günlük review |
| POST weeks/{id}/review/ | decision:approve\|dispute,reason? | employer; 5 günlük dönem itiraz hold |
| GET/POST contracts/{id}/manual-time/ | starts_at,ends_at,memo | worker; aynı interval overlap engeli |
| POST manual-time/{id}/review/ | decision:approve\|reject | employer; onay olmadan kazanç değil |
| GET/POST disputes/ | contract,milestone? veya week?,reason | taraflar; hedefli ödeme hold ve kanıt retention |
| POST disputes/{id}/resolve/ | decision:release\|refund,reason | yetkili case operator; audit; aynı ödeme ikinci kez hareket etmez |
| GET/POST contracts/{id}/ratings/ | score:1..5,comment | yalnız employer veya freelancer/leader; tek party tek rating |

## Kredi ve para

Payment DTO: id,mode:simulator|iyzico_sandbox|iyzico_live,target_type,target_id,amount,currency:TRY,status:created|pending|funded|failed|unknown|refunded,checkout_url?:string,checkout_expires_at?:ISO,provider_reference?:string,funded_at?,released_amount,refunded_amount,settlement_status:held|pending|confirmed|unavailable,error_code?. Hosted token client cevabında yok; backend saklar. checkout_url yalnız stored provider response URL. Reconcile aynı DTO; init/unknown funded sayılmaz.

Payout DTO: id,mode,amount,currency:TRY,account_name,iban_masked,status:requested|processing|paid|failed|unavailable,reserved_amount,provider_reference?,requested_at,paid_at?,failure_reason?. Bank IBAN full yalnız input/provider, UI masked; requested/processing available reserve eder, failed geri verir, paid yalnız provider transfer/reconciliation kanıtı. Released kazanç bank-paid değildir. Money DTO balance fields + ledger resultlar, ödeme ve çekim durumlarını ayrı gösterir.

Block DTO: id,client_id,session,contract,owner,starts_at,ends_at,seconds,key_count,mouse_count,active_app,screenshot?:{id,state:preview|held|released|withheld,captured_at,privacy_request?:UUID}. Screenshot blob/public URL yok; image authenticated endpoint. Privacy intent varsa ingest response state=held, owner create+hold atomik; pending request varlığında otomatik preview release olmaz.

Credit wallet: id,team?,balance,entries[],mode. Money: currency TRY,available,reserved,pending,payouts[]. Ledgerlar ayrı; bütün credits perpetual. Politika rakamları nullable; configure edilmeden maliyet/ücretsiz grant/alış fiyatı uydurulmaz. Testte yalnız staff credit grant vardır. Başlangıç/aylık grant ayarlanmışsa rol bazında tekil anahtarlarla yapılır.

| Yöntem/yol | İstek | İzin/davranış |
|---|---|---|
| GET credits/ | team? | kişi veya takım üyesi read; leader spend |
| POST boosts/ | target_type:job\|application,target_id,duration_option | yetkili owner/leader; sabit kredi yapılandırması |
| POST credit-purchases/ | credits,team? | kendi veya leader; fiyat server policy; checkout |
| POST credit-refunds/ | purchase,reason | kullanılmamış satın alma için talep; otomatik koşulsuz refund değil |
| GET money/ ; GET payments/ ; GET payouts/ | — | ilgili tarafın işlem alanı |
| POST payments/ | milestone veya week veya credit_purchase | employer/owner; amount server hedefinden türetilir |
| POST payments/{id}/reconcile/ | — | ilgili taraf; provider retrieve doğrulaması sonrası funded |
| POST payments/{id}/simulate/ | outcome:success\|failure | YALNIZ local simulator, test mode ve owner; gerçek provider başarısı değil |
| POST payouts/ | amount,iban,account_name | own available/reservation; bank request paid demek değil |
| POST payment-webhooks/iyzico/ | provider body | server retrieve/signature/id ve amount/currency/target doğrulanır |

Provider anahtarı olmayan gerçek sandbox girişimi başarı göstermez. Açıkça seçilmiş `simulator` yalnız development/test fixture; gerçek sandbox/live doğrulama değildir. Canlı iyzico held item release, refund ve bank settlement ayrı kabiliyet kapılarıdır; Mass Payout ile Marketplace aynı kazancı ikinci kez ödemez.

## Mesaj ve dosya

| Yöntem/yol | İstek | İzin/davranış |
|---|---|---|
| GET conversations/ ; GET conversations/{id}/ | — | yalnız başvuru/davet/sözleşme ilişkili party/worker |
| GET/POST conversations/{id}/messages/ | text,attachment_ids[] | yetkili, private files aynı conversation/contract kapsamı |
| POST attachments/ | multipart file,conversation? veya contract? veya job? | uploader ve scope; boyut/tür allowlist; filename güvenli |
| GET attachments/{id}/download/ | — | yalnız scope authorized; cache private,no-store; public MEDIA_URL yok |

## Tracker / görüntü

| Yöntem/yol | İstek | İzin/davranış |
|---|---|---|
| GET tracker/config/ | — | idle_seconds?, preview_seconds?, supported; desktop auth |
| GET tracker/contracts/ | — | kendi worker sözleşmeleri; fon/limit/capability durumu |
| POST tracker/sessions/ | contract,memo,client_id,monitor_id,capabilities:{screen_capture:boolean,input_counting:boolean,active_app:boolean},requested_seconds?:int | worker, canlı funded; returns session,ends_at/funding info |
| POST tracker/blocks/ | client_id,session,starts_at,ends_at,seconds,key_count,mouse_count,active_app,screenshot? (multipart PNG),captured_at?,privacy_intent?:boolean,privacy_reason?:string | tekil owner/client_id; aynı interval/seconds tutarlılığı, fon/limit ve overlap; ham key/windowtitle yok. privacy_intent true ise screenshot zorunlu, request aynı DB transaction/lock içinde yayınlanabilirlikten önce hold olur. Cevap Block DTO; tekrar aynı client UUID/digest aynı cevap |
| POST tracker/sessions/{id}/stop/ | final_client_ids[] | owner; server acknowledged bütün segmentler, pending privacy action yok; unused grant serbest |
| GET contracts/{id}/worklog/ | — | owner kendi log; employer contract worker log; teamleader başka üye screenshot görmez |
| GET screenshots/{id}/image/ | — | worker own veya ilgili employer yalnız released görüntü; case operator scoped; private/no-store |
| POST screenshots/{id}/review-ready/ | — | owner explicit önizleme bitti; publication_ready_at server now, yalnız pending privacy yoksa configuredpreview timer başlar |
| POST screenshots/{id}/publish/ | — | owner preview'da güvenli olduğunu açıkça teyit; student delete yok |
| POST screenshots/{id}/privacy/ | reason | owner employer görmeden; request hold; süre/ücret düşürmez |
| POST privacy-requests/{id}/resolve/ | decision:withhold\|publish,reason | yetkili moderator; audit; withhold orijinal private saklanır, ücret değişmez |

Preview seconds yapılandırması yoksa görüntü preview hold'da kalır; kullanıcı açık publish veya request yapabilir. Configured interval tick releases sadece talep olmayan preview. Race aynı screenshot lock'ıyla çözülür. Case görsellerinde public/signed/static URL, thumbnail/notification sızıntısı olmaz. Screenshot retention 90 gün; açık dispute aynı contract'ın ilgili kanıtlarını korur; metadata süre ledgerını silmez.

## Yönetim

GET admin/overview/; GET/POST admin/universities/ ({name,domains[]}); GET/POST admin/categories/; GET/PATCH admin/policy/ (nullable kredi/idle/preview/withdraw paramètres); POST admin/credit-grants/ ({user veya team,credits,reason}) yalnız test mode; GET admin/queue/; POST admin/reports/{id}/resolve/ ({decision:keep\|remove,reason}); POST admin/verifications/{id}/resolve/ ({decision:approve\|reject,identity_reference,company_reference?,authorized_reference?,reason}); POST admin/payouts/{id}/process/ ve credit-refunds/{id}/resolve/; GET admin/audit/. Yönetim personeli olmak bütün private görüntüleri otomatik açmaz; privacy/dispute için ilgili inceleme ilişkisinin scope'u kontrol edilir. Live doğrulama telefonun OTP kanıtı ve ayrı kimlik/kurum/yetkili dış kanıt referansları olmadan approve yapılamaz. Tutar/politika ve live provider kabiliyetleri tamamlanmadan readiness false, canlı gate fail-closed.

## Tüketici DTO ekleri — aynı sözleşmenin ayrıntıları

Profile: id,user,display_name,university,department,bio,skills[],hourly_rate,photo?,portfolio_links[]({title,url,kind}); public contact/email yok. User profile/verification/preference yalnız own auth/me cevabında. Verification: `{student:{status,student_email,verified_until},employer:{status,kind,phone_verified},payment:{status,provider_ready}}`; User.preferences `{in_app,email}`.

Config.credit_policy alanları: `post_cost,apply_cost,boost_cost,boost_hours,initial_student,initial_employer,monthly_student,monthly_employer,credit_price,withdraw_minimum` nullable. Config.tracker_policy `{idle_seconds,preview_seconds}` nullable. Admin policy aynı alanları PATCH eder; mode/readiness booleans client tarafından yazılamaz. Config.categories `[{id,name,slug}]`. Admin policies selected live parameters olmadan readiness gate geçmez. Üniversite DTO `{id,name,domains:[string]}`.

ContractChange: `{id,contract,proposer,terms,accepted_by:[UUID],status:pending|accepted|rejected,created_at}`. Contract detail `changes:[]` ve `leader_changes:[]` içerir. GET `contract-changes/` mine pending/list; POST contract-changes/{id}/accept önceki endpoint. LeadershipChange: `{id,team,new_leader,new_leader_name,payee,payee_name,contract_ids:[],approved_by:[UUID],admin_approved:boolean,status:pending|approved|rejected,reason}`. GET `leader-changes/` yetkili current/new leader veya ilgili employer/admin; Team detail `leader_changes:[]` içerir.

Worklog (`GET contracts/{id}/worklog/`) obje: `{blocks:[Block],manual_time:[{id,owner,owner_name,starts_at,ends_at,seconds,memo,status:pending|approved|rejected}],weeks:[Week],milestones:[Milestone],summary:{seconds,gross,net,currency:TRY,basis:fixed_target_amount|hourly_worked_amount}}`. Block.memo/owner_name dahil; owner dışında employer yalnız kendi sözleşmesi, leader başka worker screenshot görüntü yetkisi yok. Time metadata erişimi görüntü yetkisi değildir. Block DTO özel görüntü blob URL içermez.

Admin queue obje `{reports:[],disputes:[],privacy_requests:[],verification_requests:[],credit_refunds:[],leader_changes:[],payouts:[]}`. Ortak queue kayıt alanları `{id,status,reason,created_at}`; Reports ek job/job_title/reporter; Dispute contract/milestone?/week?/opened_by; PrivacyRequest screenshot/contract/owner/owner_name; VerificationRequest user/display_name/kind/phone_verified/legal_name/company_name? (rawidentity yok); CreditRefund purchase/wallet/credits; LeadershipChange yukarıdakiDTO; Payout yukarıdakiDTO. Audit ListPage `{id,actor,action,resource_type,resource_id,reason,created_at}`. Overview kullanıcı/jobs/contracts/open_cases sayıları yalnız gerçek DB aggregate.

Conversation DTO `{id,job?,contract?,title,participants:[{id,display_name}],updated_at}`. Message DTO `{id,sender,sender_name,text,attachments:[{id,name,size,mime}],created_at}`. Attachment upload `{id,name,size,mime}`; authenticated download relative `/api/v1/attachments/{id}/download/`, public path yok. Notification `{id,title,body,event,resource_type,resource_id,read_at,created_at}`.

Wallet DTO `{id,team,balance,mode,entries:[{id,delta,balance_after,kind,reference,created_at}]}`. Money DTO `{currency:TRY,mode,available,reserved,pending,entries:[{id,delta,kind,contract?,created_at}],payouts:[Payout]}`. CreditPurchase `{id,wallet,credits,amount,status,payment?}`; GET credit-purchases/ own/leader list ve GET credit-refunds/ kendi talep listesi. Boost `{id,target_type,target_id,credits,starts_at,ends_at,status}`; duration_option server configured option. Payout reservedamount zatenMoney.reserved'a dahil, çift düşüm yok.

GET tracker/contracts/ ListPage Contract DTO + `{tracker_ready:boolean,blocked_reason?:string,remaining_seconds?:int,funded_until?:ISO}`. Session POST cevabı `{id,contract,client_id,started_at,mode,reserved_seconds,used_seconds,authorized_until,funding:{week?,milestone?,reserved_amount,currency:TRY}}`. requested_seconds varsayılan tek600s aktif bölüm; server grant mevcut funded ortak takım saat bütçesinden kilit altında ayrılır. Her cihaz aynı shared remainingi kendi grantı gibi tüketmez. Active session grantına ait kullanılmamış limit, stop ve bütün upload ACK tamamlanmadan başka üyeye tekrar tahsis edilmez. authorized_until göreli grant sınırı/hafta sonu; offline kayıt bu yetki ve reserved_seconds içinde devam eder, yeni grant online ister. Blocks maximum active length600s, stopped session replay request same UUID accepted onlyoriginaldigest; yeni segment stop sonrasında kabul edilmez. Identity verified/student access kaybı mevcut contract çalışma iznini otomatik kaldırmaz.

## Offline grant ve privacy timeout ayrıntıları

Tracking grants aynı worker global overlap ve ortak week limit lock'ı altında tahsis edilir. Grant fonu/hours reserve, WorkBlock ile tüketim, stop ile kullanılmamış reserve ayrıdır. Expiry tek başına unuploaded süreyi başka cihaza iki kez tahsis etmez; period finalization bekleyen grantları açık inceleme işi yapar. Server durumu/review kapanışı olmayan offline hareket blind billed değildir; upload reddi local queue'da korunup destek gerekçesi gösterilir.

Wall interval de active segment seconds da <=600; idle pause son etkinlik noktasında segmenti bitirir, resume yeni segment oluşturur. Monotonic süre <=ends_at-starts_at; offline oldsegment grantın authorized capture intervalında olmalıdır. Newgrant öncesi önceki blocklar/stop senkronize olur. Desktop defaulttek600s reserve teknik capturebatchdir, sözleşmenin weeklylimitine üst iş sınırı koymaz.

Upload Block ve digest immutable. İlk dispatchten sonra privacy_intent payload değişmez. Timeout olursa aynı UUID/payload ile reconcile retry; kullanıcı sonradan privacy seçerse ayrı encrypted pendingaction(screenshot known id olunca POST privacy) kaydedilir. Upload screenshot başlangıçta `publication_ready_at=null`; tick hiçbir pending/unknown upload veya owner-review tamamlanmamış görüntüyü yayınlayamaz. Böylece id öğrenme/privacyaction retry sırasında auto release yarışı yoktur. Önizleme süresi capture zamanından değil owner explicit review-ready server receive zamanından hesaplanır; review-ready pending privacy varsa reddedilir. Publish kullanıcının explicit safeconfirm eylemidir, özel talep tamamlanmadan aktif olmaz. Bir görüntü için privacy idempotency owner/screenshot scope; terminal request retry aynı sonucu verir. Desktop local pendingprivacy tamamlana dek review-ready/publish dispatch etmez; review-ready dispatch başladıysa privacy seçimini onun sonucuna kadar kilitler. Screenshot DTO `publication_ready_at,review_due_at` ek alanlarını taşır.

Public takım keşfi: GET public-teams/ ve public-teams/{id}/ anonim, yalnız `{id,name,description,leader_name}` döndürür; private membership/wallet/contact/invites yok. Yetkili teams/ üyelik ve lider işlemi alanıdır. İlan daveti hedef seçimi publicteams UUID üzerinden yapılabilir. Boost duration_option configured boost_hours sayısının string biçimidir; server bunu kendi policy değeriyle doğrular (clienttan fiyat/süre seçimi güvenilmez). Job attachments job FK scope ile bağlanır, detail yalnız yetkili caller için attachmentmetadata; genel caller privatefile/identifier/download almaz.

Sağlayıcı hosted checkout buyer: payments/ POST optional `buyer:{first_name,last_name,phone,address,city,postal_code?,identity_number}`; simulator bu kimlik alanlarını istemez. Gerçek provider zorunlu billing eksikse unavailable/validationerror; email/IP/id authenticatedserver kaynağından. identity_number response/audit/normal DB payload yok; kalıcı outbox zorunlu hassas alanlar server envkey ile şifrelenir, plaintext saklanmaz.

POST admin/investigations/claim/ `{case_type:privacy|dispute,case_id,reason}` yetkili staff için ilgili açıkcase/contract scope grant oluşturur; `{id,contract,case_type,case_id,expires_at}` döner. Genel staff image erişimi yok; grant access audit ve expiry ile, case kapanınca yetki sona erer. UI görüntüyü incelemeden önce case claim yapar.


## Tüketici entegrasyon kesinleştirmeleri

Config ek alanları `payment_requires_buyer:boolean`, `payout_ready:boolean`, `production_readiness_missing:string[]`. `payment_ready` etkin modun fonlamayı kabul edebilmesidir; `STEP_MODE=test`, `DEBUG=true`, açık simulator fixture için true olabilir. Bu gerçek sağlayıcı/üretim readiness iddiası değildir; üretim gereksinimleri ayrı dizide görünür. Gerçek provider buyer gerektirir; simulator kimlik istemez. Milestone/Week `release_pending` ve `refund_pending` durumları sağlayıcı kuyruğunu gösterir; `released`/`refunded` yalnız doğrulanmış sonucun ardından oluşur.

GET `team-invitations/` yalnız caller'ın pending üyelikleri için ListPage `{id:teamUUID,name,description,leader_name,membership_status:invited}`; private üye/wallet/contact verisi yok. Kabul/ret mevcut POST `teams/{id}/membership/` `{action:accept|decline}`; kabul sonrası private takım erişimi açılır.

GET `admin/users/?q=` staff kullanıcı seçimi için ListPage `{id,display_name,email,roles}`; test kredi grant hedefi buradan insan adı/e-postayla seçilir. GET `contracts/{id}/worklog/` dispute incelemesinde yalnız açık dispute için caller'ın geçerli investigation grant'ıyla metadata açar. Image aynı açık case/contract grant'ını ayrıca denetler; genel staff bayrağı özel dosya/görüntü yetkisi değildir.

POST `admin/credit-refunds/{id}/resolve/` `{decision:approve|reject,reason}`. POST `admin/payouts/{id}/process/` `{reason}`; provider server tarafından seçilir, client bir transferi paid ilan edemez. Cevap ilgili güncel DTO. CreditPurchase.payment ID veya null'dır; ödeme ayrıntısı Payment endpointinden alınır.


## Son kaynak uyumu ve fixture banka akışı

Job.category Category UUID'sidir; saklama FK ile ad değişikliğinden etkilenmez. `jobs/?mine=true` ve `mine=1` yalnız kendi tüm durumlarını listeler. Category.slug isimden türetilen readonly alandır. Job private attachment metadata/download yalnız owner veya ilgili başvuru/davet/sözleşme ilişkisinin yetkili actor'ına; ilgisiz/anonim caller'a kapalı.

Contract create sabit işte `tracker_required:boolean` kabul eder; saatlikte her zaman true. Karşılıklı changes aynı alanı sabitte değiştirir; saatlik zorunluluğu kaldırmaz. Milestones değişikliğinde `{id,title,amount}` mevcut kayıtlar geçmiş durumu korur; yeni `{title,amount}` kayıtlar yeni ön fon gerektiren aşamalar olarak eklenir. ContractChange.terms bütün önerilen kapsam/revizyon/süre/takip/ücret/limit/çalışan-aşama alanlarını içerir ve karşı tarafa kabul öncesi eksiksiz gösterilir. Milestone.submission `{text,revision,attachments:[Attachment]}` olur; rawattachment id listesi tek başına teslim UI'sı değildir.

Team.active_contract_ids yalnız liderin private DTO'sında tüm aktif sözleşmeleri taşır. Leader change contract_ids boş aktif küme için [] olabilir; aktif küme varsa eksiksiz, clienttan subset alınmaz. Applications genel liste kendi bireysel teklifleri veya mevcut liderinin takım teklifleridir; işveren gelenleri explicit jobs/{id}/applications/ ile okur. Invitations genel liste caller recipient/currentleader; sent=true owner gönderilenleri ayrıca listeler.

Ödeme alıcısı kayıt cevabı gerçek provider'da `{status:onboarded,iban_masked}`; açık test+DEBUG+simulator fixture'da `{status:simulated,iban_masked,provider_verified:false}`. Fixture yalnız legal_name/iban ister; identity_number/phone/address testte istenmez. Own bank binding HMAC digest ile bütün IBAN'a bağlanır; maskedilk/sonhane eşitliği kimlik kanıtı değildir. Full IBAN gerekiyorsa envkey ile şifreli operasyon alanıdır, response/audit/plaintext DB'ye girmez.

Payout DTO ek `bank_transfer_proven:boolean`; test fixture paid durumunda false ve mode=simulator olur. UI bu sonucu yerel deneme olarak adlandırır, banka aktarımı diye göstermez. Fixture admin process `{reason,outcome:success|failure}` açık seçimi: success rezervi test payout ledgerına, failure tekrar available'a taşır. Bu gerçek transfer değildir. Gerçek provider'da process `{reason}` sadece somut provider request/reconciliation kabiliyetiyle işlem görür; `decision:reject` sadece gönderilmemiş blocked/failed talepte rezervi geri verir; unknown/processing transfer kanıtsız reject olmaz. Yetkili operator `core.change_payout` izni ve audit gerekir.

Marketplace seller settlement ve MassPayout aynı kazancı ikinci kez ödemez. Kaynak on-demand kabiliyetini varsaymaz: unavailable/blocked/processing ve missing_operation açık kalır. Bank settlement proof gerçek provider retrieval, ilgili kaynak payment/amount/currency/account binding ve tekil settlement ile doğrulanır; policy boolean veya operatör paid bayrağı kanıt değildir. Bu sağlayıcının işletmeye sunduğu kabiliyetler doğrulanmadan canlı banka çekimi hazır sayılmaz.


## Ödeme uzlaştırması ve hedefli inceleme operasyonları

Payment DTO ek `attempt:number,retry_allowed:boolean`. POST `payments/{id}/retry/` `{buyer?}` yalnız ödeme sahibi, terminal başarısız ve hiç fonlanmamış aynı hedef için kontrollü yeni checkout denemesi açar. Önceki denemenin conversation/token/terminal kanıtı PaymentAttempt geçmişinde korunur. Belirsiz initialize/retrieve sonucu yeniden başlatılmaz; önce sağlayıcıdan sorgulanır. Gerçek provider buyer zorunludur; fixture kimlik istemez. Yeni deneme istemek kredi/iş tutarını değiştirmez.

Admin queue ek alanları `payments:[Payment],provider_operations:[ProviderOperation],pending_manual_time:[ManualTime],pending_offline_grants:[WorkSession]`. ProviderOperation publicoperator DTO `{id,kind,state,payment?,attempts,error_code?,missing_operation?}`; şifreli payload, kimlik/IBAN/token ve sağlayıcı serbest metni cevapta yoktur. POST `admin/payments/{id}/reconcile/` `{reason}` ayrı `core.change_payment` yetkisi; POST `admin/provider-operations/{id}/reconcile/` `{reason}` ayrı `core.change_provideroperation` yetkisi gerektirir. Bunlar kayıtlı sağlayıcı sonucunu sorgular; operator bir ödemeyi kanıtsız paid/confirmed ilan edemez. Onboarding uzlaştırması kullanıcı dış kimliği, alıcı/banka/para birimi kanıtını kayıtlı şifreli talebe bağlar. Refund raporunun terminal sayısal statüsü resmi sözleşmede anlamlandırılmamışsa matchedmetadata tek başına başarı olmaz; missing_operation ile unknown kalır. Unknown mutasyon tick ile kör tekrarlanmaz.

İnceleme Worklog.milestones yalnız case grant kapsamında ilgili aşamaları; weeks yalnız ilgili haftaları içerir. Summary.basis `fixed_target_amount` sabit hedef bedelini, `hourly_worked_amount` saatlik onaylı/kaydedilmiş hesap toplamını belirtir; bu banka aktarımı veya kesinleşmiş kazanç kanıtı değildir. Milestone teslim metni/dosyaları aynı private kapsamdan gösterilir. Bekleyen manuel süre dönem kapanışını durdurur; employer onay/ret ve offline kayıt ACK tamamlanınca 5 günlük tam inceleme dönemi başlar. Admin bekleyen süre/yetkileri gösterir, başka actor adına kanıtsız çalışma veya süre üretmez.

Pending takım teklifinde freelancer/payee snapshotı mevcut liderle uyuşmuyorsa accept `stale_team_leader`409 verir. POST `contracts/{id}/reoffer/` `{reason}` yalnız employer, stale pending ve hiçbir ödeme denemesi/çalışma yetkisi/manuel-otomatik süre yokken mevcut koşulları yeni lider/alıcıyla tekrar karşılıklı kabul sürecine sokar. Accepted_by sıfırlanır, version ilerler ve önceki taraf/alıcı snapshotı superseded ContractChange geçmişinde saklanır. Koşullar/çalışan ücretleri bu yolla sessizce değişmez; aktif lider protokolünün yerine geçmez. Contract DTO `stale_team_leader:boolean,current_team_leader:{id,display_name}|null` onay/yeniden teklif ekranında insan tarafından görülebilir.
