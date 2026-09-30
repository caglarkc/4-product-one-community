"use client";
import { useState } from "react";
import { useSession } from "@/components/session";
import { Auth, Field, Heading, Notice, Panel, Status, TaskForm, tokens, value } from "@/components/ui";
import { date } from "@/lib/api";
function Portfolio({ links, onChange }: { links: {title:string;url:string;kind:string}[]; onChange: (links:{title:string;url:string;kind:string}[]) => void }) { return <div className="field">
<h3>Portföy bağlantıları</h3>
<p className="muted">Proje, katkı ve dış portföy bağlantıları ekleyebilirsiniz. FIRST hesabı gerekmez.</p>{links.map((link,index) => <div className="row-fields" key={index}>
<label>Başlık<input value={link.title} onChange={event => onChange(links.map((item,i) => i===index ? {...item,title:event.target.value}:item))} />
</label>
<label>Bağlantı<input type="url" value={link.url} onChange={event => onChange(links.map((item,i) => i===index ? {...item,url:event.target.value}:item))} />
</label>
<label>Bağlantı türü<select value={link.kind} onChange={event=>onChange(links.map((item,i)=>i===index?{...item,kind:event.target.value}:item))}>
<option value="portfolio">Portföy</option>
<option value="first_project">FIRST proje bağlantısı</option>
<option value="first_contribution">FIRST katkı bağlantısı</option>
</select>
</label>
<button type="button" className="text-button" onClick={() => onChange(links.filter((_,i) => i!==index))}>Kaldır</button>
</div>)}<button type="button" className="button button-small button-secondary" onClick={() => onChange([...links,{title:"",url:"",kind:"portfolio"}])}>Bağlantı ekle</button>
</div>; }
export function Account() { const { user, config, refresh } = useSession();
  const [links, setLinks] = useState<{title:string;url:string;kind:string}[] | null>(null);
  const [paymentProfile,setPaymentProfile]=useState<{status:string;iban_masked:string;provider_verified?:boolean}|null>(null);
  const simulatedProfile=config?.mode==="test"&&config.payment_provider==="simulator";
  const profile = user?.profile;
  const portfolio = links || profile?.portfolio_links || []; return <Auth>
<Heading title="Profil ve doğrulama" description="Becerilerinizi ve rolünüze ait doğrulama işlemlerini yönetin." />{config && !config.verification_required ? <Notice tone="warning">İlk ürün testinde ek öğrenci ve işveren doğrulamaları ertelenmiştir. Bu durum hesabınızı doğrulanmış saymaz.</Notice> : null}<Panel title="Profilim">
<TaskForm path="profile/" method="PATCH" fields={[{name:"university",label:"Üniversite",value:profile?.university},{name:"department",label:"Bölüm",value:profile?.department},{name:"bio",label:"Hakkımda",type:"textarea",value:profile?.bio},{name:"skills",label:"Beceriler",value:profile?.skills?.join(", "),help:"Virgülle ayırın."},{name:"hourly_rate",label:"Saatlik ücret (TL)",type:"number",min:0.01,required:true,step:"0.01",value:profile?.hourly_rate},{name:"photo",label:"Profil fotoğrafı bağlantısı",type:"url",value:profile?.photo}]} build={data => ({university:value(data,"university"),department:value(data,"department"),bio:value(data,"bio"),skills:tokens(value(data,"skills")),hourly_rate:value(data,"hourly_rate")||null,photo:value(data,"photo")||null,portfolio_links:portfolio.filter(link=>link.url && link.title)})} label="Profili kaydet" message="Profiliniz kaydedildi." onSuccess={() => refresh()}>
<Portfolio links={portfolio} onChange={setLinks} />
</TaskForm>
</Panel>
<div className="grid">
<Panel title="Öğrenci uygunluğu">
<p>Üniversite e-postası: <Status value={user?.verification?.student?.status} />
</p>
<p className="muted">Geçerlilik: {date(user?.verification?.student?.verified_until)}</p>
<TaskForm path="verification/student/" fields={[{name:"student_email",label:"Üniversite öğrenci e-postası",type:"email",required:true,value:user?.verification?.student?.student_email},{name:"birth_date",label:"Doğum tarihi",type:"date",required:true},{name:"education_level",label:"Eğitim düzeyi",type:"select",required:true,options:[{value:"associate",label:"Önlisans"},{value:"bachelor",label:"Lisans"},{value:"master",label:"Yüksek lisans"},{value:"doctorate",label:"Doktora"}]}]} label="Doğrulama e-postası gönder" message="Doğrulama e-postası gönderildi; e-postadaki bağlantıyla tamamlayın." />
<details className="details">
<summary>Mezuniyet veya e-posta erişim kaybı</summary>
<p>Mevcut işlerinizi tamamlayabilirsiniz; yeni başvurular kapanır.</p>
<TaskForm path="verification/student-status/" fields={[{name:"status",label:"Durum",type:"select",required:true,options:[{value:"graduated",label:"Mezun oldum"},{value:"access_lost",label:"Üniversite e-postama erişemiyorum"}]}]} label="Durumu bildir" onSuccess={() => refresh()} />
</details>
</Panel>
<Panel title="Telefon doğrulama">
<TaskForm path="verification/phone/start/" fields={[{name:"phone",label:"Telefon numarası",type:"tel",required:true,help:"Türkiye ülke koduyla birlikte yazın."}]} label="Doğrulama kodu gönder" message="Kod gönderimi alındı. Telefon doğrulaması kodu girdikten sonra tamamlanır." />
<TaskForm path="verification/phone/confirm/" fields={[{name:"code",label:"SMS doğrulama kodu",required:true,autoComplete:"one-time-code"}]} label="Telefonumu doğrula" message="Telefon doğrulaması kaydedildi." onSuccess={() => refresh()} />
</Panel>
</div>
<Panel title="İşveren doğrulaması">
<p>
<Status value={user?.verification?.employer?.status} />
</p>
<p>Bireysel işverende telefon ve kimlik; kurumda ayrıca kurum ve yetkili doğrulaması gerekir. Başvuru göndermek doğrulamanın tamamlanması değildir.</p>
<TaskForm path="verification/employer/" fields={[{name:"kind",label:"İşveren türü",type:"select",required:true,options:[{value:"individual",label:"Bireysel"},{value:"company",label:"Kurum"}]},{name:"phone",label:"Doğrulanmış telefon",type:"tel",required:true},{name:"legal_name",label:"Kimlikteki ad soyad",required:true},{name:"company_name",label:"Kurum unvanı"},{name:"company_registration",label:"Kurum kayıt bilgisi",help:"Kurum başvurusunda gerekli."}]} label="İnceleme başvurusu gönder" message="İşveren doğrulama başvurusu incelemeye gönderildi." onSuccess={() => refresh()} />
</Panel>
<Panel title="Kazanç ödeme bilgileri">
<p>Öğrenci uygunluğundan ayrı ödeme alıcısı kaydıdır. Kendi adınıza banka hesabı kullanın.</p>
<Status value={user?.verification?.payment?.status} />
{simulatedProfile?<Notice>Yerel kayıt denemesi yalnız ad soyad ve IBAN ister; gerçek kimlik veya sağlayıcı doğrulaması oluşturmaz.</Notice>:null}
<TaskForm<{status:string;iban_masked:string;provider_verified?:boolean}> path="payment-profile/" fields={[{name:"legal_name",label:"Banka hesabındaki ad soyad",required:true},...(simulatedProfile?[]:[{name:"phone",label:"Telefon",type:"tel" as const,required:true},{name:"identity_number",label:"T.C. kimlik numarası",type:"password" as const,required:true,autoComplete:"off"},{name:"address",label:"Adres",type:"textarea" as const,required:true}]),{name:"iban",label:"Kendi adınıza IBAN",required:true,autoComplete:"off"}]} disabled={!config} label={simulatedProfile?"Yerel ödeme alıcısı kaydını dene":"Ödeme alıcısı kaydını gönder"} clearOnSuccess message="Ödeme alıcısı kayıt sonucu alındı." onSuccess={async result=>{setPaymentProfile(result);await refresh();}} />
{paymentProfile?<Notice tone={paymentProfile.status==="simulated"||paymentProfile.provider_verified===false?"warning":"success"}>{paymentProfile.status==="simulated"||paymentProfile.provider_verified===false?"Yerel kayıt denemesi tamamlandı; sağlayıcı doğrulaması yapılmadı.":paymentProfile.status==="onboarded"?"Ödeme alıcısı kaydı yapılandırılmış sağlayıcıda oluşturuldu.":"Ödeme alıcısı kayıt durumu yenilendi."} Hesap: {paymentProfile.iban_masked}</Notice>:null}
</Panel>
<Panel title="Bildirim tercihleri">
<TaskForm path="preferences/" method="PATCH" fields={[{name:"in_app",label:"Uygulama içi bildirim",type:"checkbox",value:user?.preferences?.in_app},{name:"email",label:"E-posta bildirimi",type:"checkbox",value:user?.preferences?.email}]} label="Tercihleri kaydet" onSuccess={() => refresh()} />
</Panel>
</Auth>; }
