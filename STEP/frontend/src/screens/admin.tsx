"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useSession } from "@/components/session";
import { Action, Auth, Download, Heading, Notice, Panel, Pager, State, Status, TaskForm, tokens, usePaged, value, type FieldSpec } from "@/components/ui";
import { date, money } from "@/lib/api";
import { useResource } from "@/lib/hooks";
import type { Audit, Case, Category, PublicTeam, Queue, University, User, Worklog } from "@/lib/types";
import { ScreenshotView } from "./worklog";
import { PayoutState } from "./payments";
export function AdminNav() {return <nav className="tabs" aria-label="Yönetim alanları">
<Link href="/admin">Genel durum</Link>
<Link href="/admin/policies">Kredi ve takip ayarları</Link>
<Link href="/admin/universities">Üniversiteler</Link>
<Link href="/admin/categories">Kategoriler</Link>
<Link href="/admin/queue">İncelemeler</Link>
<Link href="/admin/audit">İşlem kaydı</Link>
</nav>;}
export function AdminHome() {const {user,config}=useSession();
  const overview=useResource<{users:number;jobs:number;contracts:number;open_cases:number}>(user?.is_staff?"admin/overview/":null);
  return <Auth staff>
<Heading title="STEP yönetimi" description="Yetkili işlemler gerekçe ve erişim kapsamıyla kaydedilir."/>
<AdminNav/>{config?.production_readiness_missing?.length?<Panel title="Canlıya hazırlık eksikleri">
<ul>{config.production_readiness_missing.map(item=>
<li key={item}>{item}</li>)}</ul>
</Panel>:null}<State loading={overview.loading} error={overview.error} retry={overview.reload}>{overview.data?<div className="grid">{[["Hesaplar",overview.data.users],["İlanlar",overview.data.jobs],["Sözleşmeler",overview.data.contracts],["Açık incelemeler",overview.data.open_cases]].map(([label,count])=>
<Panel title={String(label)} key={String(label)}>
<p className="metric">{count}</p>
</Panel>)}</div>:null}</State>
</Auth>;}
const policies:[string,string,boolean][]=[["post_cost","İlan yayınlama kredisi",true],["apply_cost","Standart başvuru kredisi",true],["boost_cost","Öne çıkarma kredisi",true],["boost_hours","Öne çıkarma süresi (saat)",true],["initial_student","Öğrenci başlangıç kredisi",true],["initial_employer","İşveren başlangıç kredisi",true],["monthly_student","Öğrenci aylık kredisi",true],["monthly_employer","İşveren aylık kredisi",true],["credit_price","Birim kredi fiyatı (TL)",false],["withdraw_minimum","Çekim alt limiti (TL)",false],["idle_seconds","Hareketsizlik eşiği (saniye)",true],["preview_seconds","Önizleme sonrası yayın bekleme (saniye)",true]];
export function AdminPolicies() {const {user,config,refresh}=useSession();
  const policy=useResource<Record<string,string|number|null>>(user?.is_staff?"admin/policy/":null);
  const [userSearch,setUserSearch]=useState("");
  const people=usePaged<User>(user?.is_staff?`admin/users/${userSearch?`?q=${encodeURIComponent(userSearch)}`:""}`:null);
  const teams=usePaged<PublicTeam>(user?.is_staff?"public-teams/":null);
  return <Auth staff>
<Heading title="Kredi ve takip ayarları"/>
<AdminNav/>
<Notice tone="warning">Boş alan belirlenmemiştir. Canlı işlemler gerekli ayar tamamlanmadan açılmaz; burada sağlayıcı anahtarı veya canlı hazırlık durumunu değiştiremezsiniz.</Notice>
<Panel title="Politika değerleri">
<State loading={policy.loading} error={policy.error} retry={policy.reload}>{policy.data?<TaskForm path="admin/policy/" method="PATCH" fields={[...policies.map(([name,label,integer])=>({name,label,type:"number" as const,min:0,step:integer?"1":"0.01",value:policy.data?.[name]??"",help:"Boş bırakırsanız belirlenmemiş olarak kaydedilir."})),{name:"withdraw_schedule",label:"Ödeme / banka çekim takvimi",value:policy.data?.withdraw_schedule??"",help:"Operasyon ve sağlayıcıyla belirlenmiş takvimi yazın. Boşsa henüz belirlenmemiştir."}]} build={data=>({...Object.fromEntries(policies.map(([name,,integer])=>[name,value(data,name)===""?null:integer?Number(value(data,name)):value(data,name)])),withdraw_schedule:value(data,"withdraw_schedule")||null})} label="Politikayı kaydet" onSuccess={async()=>{policy.reload();await refresh();}}/>:null}</State>
</Panel>
<Panel title="Test kredisi ver">
<label className="field">Kredi verilecek kullanıcıyı ara<input type="search" value={userSearch} onChange={event=>setUserSearch(event.target.value)}/>
</label>{config?.mode==="live"?<Notice>Canlı ortamda test kredisi verilemez.</Notice>:<>
<TaskForm path="admin/credit-grants/" fields={[{name:"user",label:"Kullanıcı",type:"select",options:people.items.map(person=>({value:person.id,label:`${person.display_name||"Kullanıcı"} · ${person.email}`}))},{name:"team",label:"Takım",type:"select",options:teams.items.map(team=>({value:team.id,label:team.name}))},{name:"credits",label:"Test kredisi miktarı",type:"number",required:true,min:1,step:"1"},{name:"reason",label:"Gerekçe",type:"textarea",required:true}]} build={data=>({... (value(data,"team")?{team:value(data,"team")}:{user:value(data,"user")}),credits:Number(value(data,"credits")),reason:value(data,"reason")})} label="Test kredisi kaydet" disabled={people.loading||teams.loading||Boolean(people.error||teams.error)} message="Test kredisi kaydedildi; canlı ücretsiz hak veya gerçek kazanç değildir."/>
<State loading={people.loading||teams.loading} error={people.error||teams.error} retry={()=>{people.reload();teams.reload();}}><Pager {...people}/><Pager {...teams}/></State>
</>}</Panel>
</Auth>;}
export function AdminUniversities() {const {user}=useSession();
  const universities=usePaged<University>(user?.is_staff?"admin/universities/":null);
  return <Auth staff>
<Heading title="Üniversite alan adları" description="Öğrenci e-postası kabul listesi yönetim tarafından tanımlanır."/>
<AdminNav/>
<Panel title="Üniversite ekle">
<TaskForm path="admin/universities/" fields={[{name:"name",label:"Üniversite adı",required:true},{name:"domains",label:"Öğrenci e-posta alan adları",required:true,help:"Virgülle ayırın. Yalnız alan adı yazın."}]} build={data=>({name:value(data,"name"),domains:tokens(value(data,"domains"))})} label="Üniversiteyi ekle" onSuccess={universities.reload}/>
</Panel>
<State loading={universities.loading} error={universities.error} retry={universities.reload}>{universities.items.map(item=>
<Panel key={item.id} title={item.name}>
<p>{item.domains.join(" · ")}</p>
<TaskForm path={`admin/universities/${item.id}/`} method="PATCH" fields={[{name:"name",label:"Üniversite adı",required:true,value:item.name},{name:"domains",label:"Öğrenci alan adları",required:true,value:item.domains.join(", ")}]} build={data=>({name:value(data,"name"),domains:tokens(value(data,"domains"))})} label="Alan adlarını güncelle" onSuccess={universities.reload}/>
</Panel>)}<Pager {...universities}/>
</State>
</Auth>;}
export function AdminCategories() {const {user,refresh}=useSession();
  const categories=usePaged<Category>(user?.is_staff?"admin/categories/":null);
  return <Auth staff>
<Heading title="İş kategorileri"/>
<AdminNav/>
<Panel title="Kategori ekle">
<TaskForm path="admin/categories/" fields={[{name:"name",label:"Kategori adı",required:true}]} label="Kategoriyi ekle" onSuccess={async()=>{categories.reload();await refresh();}}/>
</Panel>
<State loading={categories.loading} error={categories.error} retry={categories.reload}>{categories.items.map(item=>
<Panel key={item.id} title={item.name}>
<TaskForm path={`admin/categories/${item.id}/`} method="PATCH" fields={[{name:"name",label:"Kategori adı",required:true,value:item.name}]} label="Kategoriyi güncelle" onSuccess={async()=>{categories.reload();await refresh();}}/>
</Panel>)}<Pager {...categories}/>
</State>
</Auth>;}
function Investigation({item,type,onReady}:{item:Case;type:"privacy"|"dispute";onReady?:(ready:boolean)=>void}) {
  const [grant,setGrant]=useState<{contract:string;expires_at:string}|null>(null);
  const log=useResource<Worklog>(grant&&type==="dispute"?`contracts/${grant.contract}/worklog/`:null);
  const milestone=log.data?.milestones?.find(stage=>stage.id===item.milestone);
  const week=log.data?.weeks.find(period=>period.id===item.week);
  const ready=Boolean(grant&&type==="dispute"&&!log.loading&&!log.error&&log.data&&((milestone&&log.data.summary.basis==="fixed_target_amount")||(week&&log.data.summary.basis==="hourly_worked_amount")));
  useEffect(()=>{onReady?.(ready);},[ready,onReady]);
  useEffect(()=>{if(!grant)return;const timer=window.setTimeout(()=>setGrant(null),Math.max(0,new Date(grant.expires_at).getTime()-Date.now()));return()=>window.clearTimeout(timer);},[grant]);
  return <details className="details">
    <summary>Yetkili kanıt incelemesi</summary>
    <p>Görüntülere yalnız ilgili açık inceleme için geçici yetki alarak erişebilirsiniz.</p>
    <TaskForm<{contract:string;expires_at:string}> path="admin/investigations/claim/" fields={[{name:"reason",label:"Erişim gerekçesi",type:"textarea",required:true}]} build={data=>({case_type:type,case_id:item.id,reason:value(data,"reason")})} label="Bu inceleme için erişim iste" message="İncelemeye özel geçici erişim verildi." onSuccess={setGrant}/>
    {grant?<><p className="muted">Erişim sonu: {date(grant.expires_at)}</p>{type==="privacy"&&item.screenshot?<ScreenshotView screenshot={{id:item.screenshot,state:"held",captured_at:""}} own={false} permitted refresh={()=>{}}/>:<State loading={log.loading} error={log.error} retry={log.reload}>{log.data?<>
      <h4>İtiraz konusu ve bedeli</h4>{milestone?<article className="card"><h5>{milestone.title}</h5><Status value={milestone.status}/><p>Aşama iş bedeli: {money(milestone.amount)}</p>{milestone.review_due_at?<p>İnceleme sonu: {date(milestone.review_due_at)}</p>:null}{typeof milestone.submission==="object"&&milestone.submission?<><p className="long-text">{milestone.submission.text}</p>{milestone.submission.attachments?.map(file=><Download key={file.id} attachment={file}/>)}</>:<p>Bu aşama için teslim kaydı yok.</p>}</article>:week?<article className="card"><h5>{date(week.starts_at)} — {date(week.ends_at)}</h5><Status value={week.status}/><p>Ortak sınır: {week.limit_hours} saat · Fon: {money(week.reserved_amount)}</p><p>Çalışılan: {(week.worked_seconds/3600).toFixed(2)} saat · Brüt: {money(week.gross)} · Net: {money(week.net)}</p>{week.review_due_at?<p>İnceleme sonu: {date(week.review_due_at)}</p>:null}</article>:<Notice tone="warning">İtirazın hedef aşaması veya haftası alınamadı. Karar verilemez.</Notice>}
      <h4>{log.data.summary.basis==="fixed_target_amount"?"İtiraz edilen sabit iş bedeli":log.data.summary.basis==="hourly_worked_amount"?"Saatlik çalışma hesabı":"Hesap esası alınamadı"}</h4><p className="muted">Bu tutarlar banka aktarımı veya kesinleşmiş kazanç kanıtı değildir.</p><p>{(log.data.summary.seconds/3600).toFixed(2)} saat · Brüt {money(log.data.summary.gross)} · Net {money(log.data.summary.net)}</p>
      <h4>Masaüstü çalışma kayıtları</h4>{log.data.blocks.map(block=><div className="card" key={block.id}><p>{block.owner_name||"Çalışan"} · {date(block.starts_at)} — {date(block.ends_at)} · {(block.seconds/60).toFixed(1)} dakika</p><p>{block.memo}</p><p className="muted">Uygulama: {block.active_app} · Klavye: {block.key_count} · Fare: {block.mouse_count}</p>{block.screenshot?<ScreenshotView screenshot={block.screenshot} own={false} permitted refresh={log.reload}/>:null}</div>)}{!log.data.blocks.length?<p>Bu inceleme kapsamında masaüstü kaydı yok.</p>:null}
      <h4>Manuel çalışma ve işveren kararları</h4>{log.data.manual_time.map(record=><article className="card" key={record.id}><p>{record.owner_name||"Çalışan"} · {date(record.starts_at)} — {date(record.ends_at)}</p><p>{((record.seconds??0)/60).toFixed(1)} dakika · <Status value={record.status}/></p><p className="long-text">{record.memo}</p></article>)}{!log.data.manual_time.length?<p>Bu inceleme kapsamında manuel süre yok.</p>:null}
    </>:null}</State>}</>:null}
  </details>;
}
function QueueCard({item,kind,refresh}:{item:Case;kind:string;refresh:()=>void}) {const {config}=useSession(); const [evidenceReady,setEvidenceReady]=useState(false); const simulated=item.mode==="simulator"&&config?.mode==="test"&&config.payment_provider==="simulator"; const decisions:FieldSpec={name:"decision",label:"Karar",type:"select",required:true,options:[{value:"approve",label:"Onayla"},{value:"reject",label:"Reddet"}]};
  return <article className="card">
<h3>{item.job_title||item.display_name||item.owner_name||"İnceleme kaydı"}</h3>
{kind==="payouts"?<PayoutState payout={{mode:item.mode||"unknown",status:item.status,bank_transfer_proven:item.bank_transfer_proven===true}}/>:<Status value={item.status}/>} {item.reason?<p>{item.reason}</p>:null}{item.amount?<p>{money(item.amount)}</p>:null}{kind==="reports"?<TaskForm path={`admin/reports/${item.id}/resolve/`} fields={[{...decisions,options:[{value:"keep",label:"İlanı koru"},{value:"remove",label:"İlanı kaldır"}]},{name:"reason",label:"Karar gerekçesi",type:"textarea",required:true}]} label="Şikâyeti sonuçlandır" onSuccess={refresh}/>:null}{kind==="disputes"?<>
<Investigation item={item} type="dispute" onReady={setEvidenceReady}/>
{!evidenceReady?<Notice tone="warning">Geçici inceleme yetkisi ve hedef işin kanıtları yüklenmeden ödeme kararı açılamaz.</Notice>:null}
<TaskForm path={`disputes/${item.id}/resolve/`} fields={[{...decisions,options:[{value:"release",label:"İlgili ödemeyi serbest bırak"},{value:"refund",label:"İlgili tutarı iade et"}]},{name:"reason",label:"Çözüm gerekçesi",type:"textarea",required:true}]} label="İtirazı sonuçlandır" disabled={!evidenceReady} onSuccess={refresh}/>
</>:null}{kind==="privacy_requests"?<>
<Investigation item={item} type="privacy"/>
<TaskForm path={`privacy-requests/${item.id}/resolve/`} fields={[{...decisions,options:[{value:"withhold",label:"Görüntüyü özel sakla"},{value:"publish",label:"Görüntüyü yayımla"}]},{name:"reason",label:"Moderasyon gerekçesi",type:"textarea",required:true}]} label="Görüntü incelemesini sonuçlandır" onSuccess={refresh}/>
</>:null}{kind==="verification_requests"?<>
<p>Telefon OTP: {item.phone_verified?"Teyit edilmiş":"Eksik"}</p>
<p>{item.legal_name} · {item.company_name}</p>
<TaskForm path={`admin/verifications/${item.id}/resolve/`} fields={[decisions,{name:"identity_reference",label:"Yetkili kimlik kontrolü kanıt referansı"},{name:"company_reference",label:"Kurum kontrolü kanıt referansı"},{name:"authorized_reference",label:"Yetkili kişi kontrolü kanıt referansı"},{name:"reason",label:"Karar gerekçesi",type:"textarea",required:true}]} label="Doğrulama kararını kaydet" message="Karar kaydedildi; canlı uygunluk dış kanıt ve telefon kontrolüne tabidir." onSuccess={refresh}/>
</>:null}{kind==="credit_refunds"?<TaskForm path={`admin/credit-refunds/${item.id}/resolve/`} fields={[decisions,{name:"reason",label:"İade karar gerekçesi",type:"textarea",required:true}]} label="Kredi iade talebini sonuçlandır" message="İade talebi kararı kaydedildi; sağlayıcı iade sonucu ayrı doğrulanır." onSuccess={refresh}/>:null}{kind==="leader_changes"?<>
<p>Yeni lider: {item.new_leader_name||"Seçilen kişi"} · Mevcut işlerin ödeme alıcısı: {item.payee_name||"Seçilen kişi"}</p>
<Action path={`leader-changes/${item.id}/approve/`} label="Lider değişikliğini ve belirtilen ödeme alıcısını onayla" onSuccess={refresh}/>
</>:null}{kind==="payouts"?<>
<p>{item.account_name} · {item.iban_masked}</p>
{simulated?<><Notice>Yerel çekim denemesi; banka transferi yapılmaz. Başarısız sonuç test rezervini kullanılabilir bakiyeye döndürür.</Notice><TaskForm path={`admin/payouts/${item.id}/process/`} fields={[{name:"outcome",label:"Yerel çekim sonucu",type:"select",required:true,options:[{value:"success",label:"Yerel başarılı sonuç"},{value:"failure",label:"Yerel başarısız sonuç"}]},{name:"reason",label:"Test işlem gerekçesi",type:"textarea",required:true}]} label="Yerel çekim denemesini sonuçlandır" message="Yerel çekim sonucu kaydedildi; gerçek banka aktarımı değildir." onSuccess={refresh}/></>:<><TaskForm path={`admin/payouts/${item.id}/process/`} fields={[{name:"reason",label:"Aktarım işlem gerekçesi",type:"textarea",required:true}]} label="Banka aktarım sonucunu kontrol et" message="Çekim durumu sağlayıcıdan kontrol edildi. Ödendi durumu yalnız banka aktarım kanıtıyla belirlenir." onSuccess={refresh}/>{["unavailable","failed"].includes(item.status)?<details className="details"><summary>Gönderilmemiş talebi reddet</summary><p>Sunucu talebin sağlayıcıya gönderilmediğini doğrularsa rezerv geri verilir. Sonucu bilinmeyen veya işlenen transfer bu işlemle reddedilmez.</p><TaskForm path={`admin/payouts/${item.id}/process/`} fields={[{name:"reason",label:"Ret gerekçesi",type:"textarea",required:true}]} build={data=>({decision:"reject",reason:value(data,"reason")})} label="Gönderilmemiş talebi reddet" message="Çekim ret sonucu sunucudan alındı." onSuccess={refresh}/></details>:null}</>}
</>:null}</article>;}
function OperationCard({item,kind,refresh}:{item:Case;kind:"payments"|"provider_operations"|"pending_manual_time"|"pending_offline_grants";refresh:()=>void}) {
  if(kind==="pending_offline_grants")return <article className="card"><h3>Senkronizasyonu beklenen çalışma yetkisi</h3><p>Yetkinin sonu: {date(item.authorized_until)}</p><p>Ayrılan süre: {((item.reserved_seconds??0)/60).toFixed(1)} dakika · Kaydedilen: {((item.used_seconds??0)/60).toFixed(1)} dakika</p><p className="muted">Kapanmamış yerel kayıtların istemciden senkronize olması gerekir. Yönetim bu ekrandan süre üretmez veya kanıtsız kapatma yapmaz.</p></article>;
  if(kind==="pending_manual_time")return <article className="card"><h3>{item.owner_name||"Çalışan"} · Manuel süre onayı bekliyor</h3><Status value={item.status}/><p>{date(item.starts_at)} — {date(item.ends_at)} · {((item.seconds??0)/60).toFixed(1)} dakika</p><p>{item.memo}</p><p className="muted">Bu sürenin ücretlendirme kararı ilgili işverene aittir. Yönetim bu ekrandan başkasının işveren onayını vermez.</p></article>;
  const targetLabel=item.target_type==="milestone"?"Aşama fonlaması":item.target_type==="week"?"Haftalık fonlama":item.target_type==="credit_purchase"?"Kredi satın alma":"Ödeme işlemi";
  return <article className="card"><h3>{kind==="payments"?targetLabel:"Sağlayıcı işlemi"}</h3><Status value={kind==="payments"?item.status:item.state}/>{item.mode?<Status value={item.mode}/>:null}{kind==="payments"?<><p>{money(item.amount)} · Deneme {item.attempt??"Belirtilmedi"}</p><p>Serbest bırakılan {money(item.released_amount)} · İade edilen {money(item.refunded_amount)}</p><p>{item.mode==="simulator"?"Yerel deneme mutabakatı":"Banka sonucu"}: <Status value={item.settlement_status}/></p></>:<p>İşlem: {item.kind||"Belirtilmedi"} · Deneme {item.attempts??"Belirtilmedi"}</p>}{item.error_code?<Notice tone="warning">Sağlayıcı sonucu: {item.error_code}</Notice>:null}{item.missing_operation?<Notice tone="warning">Tamamlanması gereken sağlayıcı işlemi: {item.missing_operation}</Notice>:null}<p className="muted">Bu kontrol yeni bir ödeme veya kanıtsız banka aktarımı oluşturmaz. Hazır olmayan ve sonucu bilinmeyen işlemler doğrulanana kadar bekler.</p><TaskForm path={kind==="payments"?`admin/payments/${item.id}/reconcile/`:`admin/provider-operations/${item.id}/reconcile/`} fields={[{name:"reason",label:"Sağlayıcı sonuç kontrolü gerekçesi",type:"textarea",required:true}]} label="Sağlayıcı sonucunu kontrol et" message="Sağlayıcı sonucu kontrol edildi; tamamlanma yalnız doğrulanmış kanıtla gösterilir." onSuccess={refresh}/></article>;
}
const queueLabels:[string,string][]=[["reports","İlan şikâyetleri"],["disputes","İş bedeli itirazları"],["privacy_requests","Kişisel bilgi görüntü talepleri"],["verification_requests","İşveren doğrulamaları"],["credit_refunds","Kredi iade talepleri"],["leader_changes","Lider değişiklikleri"],["payouts","Banka çekim talepleri"],["payments","Kontrol bekleyen ödemeler"],["provider_operations","Sağlayıcı işlemleri"],["pending_manual_time","İşveren onayı bekleyen manuel süreler"],["pending_offline_grants","Senkronizasyonu beklenen çalışma yetkileri"]];
export function AdminQueue() {const {user}=useSession();
  const queue=useResource<Queue>(user?.is_staff?"admin/queue/":null);
  return <Auth staff>
<Heading title="İnceleme ve işlem kuyruğu" description="Her işlem kendi kapsamı, gerekçesi ve sağlayıcı durumu üzerinden yürütülür."/>
<AdminNav/>
<State loading={queue.loading} error={queue.error} retry={queue.reload}>{queue.data?queueLabels.map(([kind,label])=>
<Panel title={label} key={kind}>{!Array.isArray(queue.data?.[kind])?<Notice tone="warning">Bu kuyruğun verisi sunucudan alınamadı.</Notice>:queue.data[kind].length?queue.data[kind].map(item=>
["payments","provider_operations","pending_manual_time","pending_offline_grants"].includes(kind)?<OperationCard item={item} kind={kind as "payments"|"provider_operations"|"pending_manual_time"|"pending_offline_grants"} key={item.id} refresh={queue.reload}/>:<QueueCard item={item} kind={kind} key={item.id} refresh={queue.reload}/>):<p className="empty">Bekleyen kayıt yok.</p>}</Panel>):null}</State>
</Auth>;}
export function AdminAudit() {const {user}=useSession();
  const audit=usePaged<Audit>(user?.is_staff?"admin/audit/":null);
  return <Auth staff>
<Heading title="Yönetim işlem kaydı" description="Kimlik bilgileri, sağlayıcı sırları ve özel görüntüler işlem kaydında gösterilmez."/>
<AdminNav/>
<State loading={audit.loading} error={audit.error} retry={audit.reload}>
<Panel>
<div className="table-wrap">
<table>
<thead>
<tr>
<th>İşlem</th>
<th>Kaynak</th>
<th>Gerekçe</th>
<th>Tarih</th>
</tr>
</thead>
<tbody>{audit.items.map(item=>
<tr key={item.id}>
<td>{item.action}</td>
<td>{item.resource_type||item.resource}</td>
<td>{item.reason}</td>
<td>{date(item.created_at)}</td>
</tr>)}</tbody>
</table>
</div>
<Pager {...audit}/>
</Panel>
</State>
</Auth>;}
