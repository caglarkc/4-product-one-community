"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useSession } from "@/components/session";
import { Action, Auth, Download, FilePicker, Heading, Notice, Panel, Pager, State, Status, TaskForm, usePaged, value, type FieldSpec } from "@/components/ui";
import { date, localISO, money } from "@/lib/api";
import { useResource, useCollection } from "@/lib/hooks";
import type { Application, Attachment, Contract, Job, Milestone, PublicProfile, Rating, Week, Worklog } from "@/lib/types";
import { Funding } from "./payments";
import { WorklogSection } from "./worklog";
import { ContractChangeCard } from "./contract-terms";
export function Contracts() { const {user}=useSession();
  const contracts=usePaged<Contract>(user?"contracts/":null); return <Auth>
<Heading title="Sözleşmeler" description="Her işe alımın koşulları, fonları ve özel çalışma alanı ayrıdır."/>
<State loading={contracts.loading} error={contracts.error} empty={!contracts.items.length} retry={contracts.reload}>{contracts.items.map(contract=>
<article className="card" key={contract.id}>
<h2>
<Link href={`/contracts/${contract.id}`}>{contract.job_title||contract.scope.slice(0,90)}</Link>
</h2>
<div className="meta">
<Status value={contract.status}/>
<Status value={contract.work_type}/>
<span>{contract.expected_duration}</span>
</div>
<p>{contract.scope.slice(0,240)}</p>
<p className="muted">{contract.team?"Takım sözleşmesi":"Bireysel sözleşme"} · Saatlik takip {contract.tracker_required?"gerekli":"tercihe bağlı"}</p>
</article>)}<Pager {...contracts}/>
</State>
</Auth>; }
interface StageDraft { title:string; amount:string }
interface WorkerDraft { user:string; hourly_rate:string; display_name?:string }
function StageEditor({stages,setStages}:{stages:StageDraft[];setStages:(value:StageDraft[])=>void}) {return <div className="field">
<h3>Aşamalar</h3>{stages.map((stage,index)=>
<div className="row-fields" key={index}>
<label>Aşama başlığı<input required value={stage.title} onChange={event=>setStages(stages.map((item,i)=>i===index?{...item,title:event.target.value}:item))}/>
</label>
<label>Bedel (TL)<input type="number" step="0.01" min="0.01" required value={stage.amount} onChange={event=>setStages(stages.map((item,i)=>i===index?{...item,amount:event.target.value}:item))}/>
</label>
<button type="button" className="text-button" disabled={stages.length===1} onClick={()=>setStages(stages.filter((_,i)=>i!==index))}>Kaldır</button>
</div>)}<button className="button button-small button-secondary" type="button" onClick={()=>setStages([...stages,{title:"",amount:""}])}>Aşama ekle</button>
</div>;}
function WorkerEditor({workers,setWorkers,people}:{workers:WorkerDraft[];setWorkers:(value:WorkerDraft[])=>void;people:PublicProfile[]}) {return <div className="field">
<h3>İşe dahil öğrenciler ve saatlik ücretleri</h3>{workers.map((worker,index)=>
<div className="row-fields" key={index}>
<label>Öğrenci<select required value={worker.user} onChange={event=>setWorkers(workers.map((item,i)=>i===index?{...item,user:event.target.value,display_name:people.find(person=>(person.user||person.id)===event.target.value)?.display_name}:item))}>
<option value="">Öğrenciyi seçin</option>{worker.user&&!people.some(person=>(person.user||person.id)===worker.user)?<option value={worker.user}>{worker.display_name||"Seçilen öğrenci"}</option>:null}{people.map(person=>
<option key={person.id} value={person.user||person.id}>{person.display_name||"Öğrenci"}</option>)}</select>
</label>
<label>Saatlik ücret (TL)<input required type="number" step="0.01" min="0.01" value={worker.hourly_rate} onChange={event=>setWorkers(workers.map((item,i)=>i===index?{...item,hourly_rate:event.target.value}:item))}/>
</label>
<button type="button" className="text-button" onClick={()=>setWorkers(workers.filter((_,i)=>i!==index))}>Kaldır</button>
</div>)}<button type="button" className="button button-small button-secondary" onClick={()=>setWorkers([...workers,{user:"",hourly_rate:""}])}>Çalışan öğrenci ekle</button>
<small>Takım üyeliği ve uygunluk sunucuda kontrol edilir. Ortak haftalık sınır tüm üyelerin toplamına uygulanır.</small>
</div>;}
export function NewContract() {
  const {user}=useSession();
  const router=useRouter();
  const [jobId,setJobId]=useState("");
  const [applicationId,setApplicationId]=useState("");
  const [stages,setStages]=useState<StageDraft[]>([{title:"",amount:""}]);
  const [workers,setWorkers]=useState<WorkerDraft[]>([]);
  useEffect(()=>{const params=new URLSearchParams(window.location.search);setJobId(params.get("job")||"");setApplicationId(params.get("application")||"");},[]);
  const jobs=usePaged<Job>(user?"jobs/?mine=true":null);
  const job=useResource<Job>(jobId?`jobs/${jobId}/`:null);
  const applications=useCollection<Application>(jobId?`jobs/${jobId}/applications/`:null);
  const people=useCollection<PublicProfile>(user?"profiles/":null);
  const chosen=applications.items.find(item=>item.id===applicationId);
  const hourly=job.data?.work_type==="hourly";
  return <Auth>
<Heading title="Sözleşme hazırla" description="Koşullar iki taraf kabul edene kadar taslaktır. Çalışma ilgili fonlama doğrulandıktan sonra başlar."/>
<Panel>
<State loading={jobs.loading} error={jobs.error} retry={jobs.reload}><p className="muted">İlan seçimi hazır.</p></State>
<label className="field">İlan<select disabled={jobs.loading||Boolean(jobs.error)} value={jobId} onChange={event=>{setJobId(event.target.value);setApplicationId("");}}>
<option value="">İlan seçin</option>{job.data&&!jobs.items.some(item=>item.id===jobId)?<option value={jobId}>{job.data.title}</option>:null}{jobs.items.map(item=>
<option key={item.id} value={item.id}>{item.title}</option>)}</select>
</label>
<Pager {...jobs}/>
<label className="field">Seçilecek başvuru<select disabled={applications.loading||Boolean(applications.error)} value={applicationId} onChange={event=>setApplicationId(event.target.value)}>
<option value="">Başvuru seçin</option>{applications.items.map(item=>
<option key={item.id} value={item.id}>{item.team_name||item.student_name||"Öğrenci başvurusu"} · {money(item.price)} · {item.duration}</option>)}</select>
</label>
<p className="muted">{applications.items.length} başvuru</p>
<State loading={job.loading||applications.loading} error={job.error||applications.error} retry={()=>{job.reload();applications.reload();}}>{chosen&&job.data?<>
<p className="long-text">{chosen.cover_letter}</p>{chosen.team?<State loading={people.loading} error={people.error} retry={people.reload}><p className="muted">{people.items.length} öğrenci seçime hazır.</p></State>:null}
<TaskForm<Contract> path="contracts/" fields={[{name:"scope",label:"Kabul edilecek iş kapsamı",type:"textarea",required:true,value:job.data.description},{name:"expected_duration",label:"Beklenen süre",required:true,value:chosen.duration},{name:"revision_terms",label:"Revizyon koşulları",type:"textarea",required:true},{name:"weekly_limit",label:"Ortak haftalık saat sınırı",type:"number",min:0.01,step:"0.01",required:hourly,help:"Saatlik işte tüm çalışanların toplam sınırı."},{name:"tracker_required",label:"Sabit işte masaüstü takip kullanılsın",type:"checkbox",help:"Saatlik işte takip zaten zorunludur."}]} build={data=>({application:chosen.id,scope:value(data,"scope"),expected_duration:value(data,"expected_duration"),revision_terms:value(data,"revision_terms"),...(hourly?{weekly_limit:value(data,"weekly_limit")}:{milestones:stages}),tracker_required:hourly||data.has("tracker_required"),members:chosen.team?workers.map(({user,hourly_rate})=>({user,hourly_rate})):[{user:chosen.student,hourly_rate:chosen.price}]})} label="Sözleşme taslağını oluştur" message="Sözleşme oluşturuldu. Tarafların kabulü bekleniyor." disabled={jobs.loading||Boolean(jobs.error)||applications.loading||Boolean(applications.error)||Boolean(chosen.team&&(!workers.length||people.loading||people.error))} onSuccess={contract=>router.push(`/contracts/${contract.id}`)}>{!hourly?<StageEditor stages={stages} setStages={setStages}/>:null}{chosen.team?<>
<WorkerEditor workers={workers} setWorkers={setWorkers} people={people.items}/>

</>:null}</TaskForm>
</>:<p className="muted">İlan ve başvuruyu seçerek devam edin.</p>}</State>
</Panel>
</Auth>;
}
function MilestoneCard({milestone,contract,employer,worker,refresh}:{milestone:Milestone;contract:Contract;employer:boolean;worker:boolean;refresh:()=>void}) {const [files,setFiles]=useState<Attachment[]>([]);
  const reviewable=milestone.status==="submitted";
  return <article className="card">
<h3>{milestone.title}</h3>
<div className="meta">
<Status value={milestone.status}/>
<span>{money(milestone.amount)}</span>
</div>{milestone.review_due_at?<p>İnceleme sonu: {date(milestone.review_due_at)}</p>:null}{typeof milestone.submission==="object"&&milestone.submission?<>
<p className="long-text">{milestone.submission.text}</p>{milestone.submission.attachments?.map(file=>
<Download key={file.id} attachment={file}/>)}</>:null}{employer&&milestone.status==="unfunded"?<Funding target={{milestone:milestone.id}} onFunded={refresh}/>:null}{worker&&milestone.status==="funded"?<Action path={`milestones/${milestone.id}/start/`} label="Aşamada çalışmaya başla" onSuccess={refresh}/>:null}{worker&&["funded","in_progress","revision"].includes(milestone.status)?<details className="details">
<summary>Teslim veya yeniden teslim</summary>
<TaskForm path={`milestones/${milestone.id}/submit/`} fields={[{name:"text",label:"Teslim açıklaması",type:"textarea",required:true}]} build={data=>({text:value(data,"text"),attachment_ids:files.map(file=>file.id)})} label="Teslimi gönder" message="Teslim kaydedildi. 14 günlük inceleme süresi bu teslimden başlar." onSuccess={refresh}>
<FilePicker scope={{contract:contract.id}} onChange={setFiles}/>
</TaskForm>
</details>:null}{employer&&reviewable?<TaskForm path={`milestones/${milestone.id}/review/`} fields={[{name:"decision",label:"Teslim incelemesi",type:"select",required:true,options:[{value:"approve",label:"Teslimi onayla"},{value:"revision",label:"Sözleşme koşullarıyla revizyon iste"},{value:"dispute",label:"İtiraz aç ve ödemeyi beklet"}]},{name:"reason",label:"Açıklama",type:"textarea"}]} label="İnceleme kararını gönder" onSuccess={refresh}/>:null}</article>;}
function WeekCard({week,employer,refresh}:{week:Week;employer:boolean;refresh:()=>void}) {return <article className="card">
<h3>{date(week.starts_at)} — {date(week.ends_at)}</h3>
<div className="meta">
<Status value={week.status}/>
<span>Ortak sınır {week.limit_hours} saat</span>
<span>Fon {money(week.reserved_amount)}</span>
</div>
<p>{(week.worked_seconds/3600).toFixed(2)} saat · Brüt {money(week.gross)} · Net {money(week.net)}</p>{week.review_due_at?<p>İtiraz/inceleme sonu: {date(week.review_due_at)}</p>:null}{employer&&week.status==="unfunded"?<Funding target={{week:week.id}} onFunded={refresh}/>:null}{employer&&week.status==="funded"?<Action path={`weeks/${week.id}/close/`} label="Haftayı incelemeye kapat" onSuccess={refresh} message="Hafta kapanış isteği alındı. Bekleyen manuel veya yerel kayıtlar tamamlandıktan sonra inceleme başlar."/>:null}{employer&&week.status==="review"?<TaskForm path={`weeks/${week.id}/review/`} fields={[{name:"decision",label:"Haftalık karar",type:"select",required:true,options:[{value:"approve",label:"Onayla"},{value:"dispute",label:"İtiraz aç"}]},{name:"reason",label:"Açıklama",type:"textarea"}]} label="Haftalık incelemeyi gönder" onSuccess={refresh}/>:null}</article>;}
export function ContractDetail() {
  const {id}=useParams<{id:string}>();
  const {user}=useSession();
  const contract=useResource<Contract>(user?`contracts/${id}/`:null);
  const log=useResource<Worklog>(user?`contracts/${id}/worklog/`:null);
  const ratings=usePaged<Rating>(user?`contracts/${id}/ratings/`:null);
  const c=contract.data;
  const employer=c?.employer===user?.id;
  const representative=c?.freelancer===user?.id;
  const worker=Boolean(c&&(representative||c.members.some(member=>member.user===user?.id)));
  const [newStages,setNewStages]=useState<StageDraft[]>([]);
  const [newWorkers,setNewWorkers]=useState<WorkerDraft[]|null>(null);
  const peopleNeeded=Boolean(c?.team||c?.changes?.some(change=>change.terms?.members));
  const people=useCollection<PublicProfile>(peopleNeeded?"profiles/":null);
  const refresh=()=>{contract.reload();log.reload();};
  const changeFields:FieldSpec[]=c?[{name:"scope",label:"Yeni kapsam",type:"textarea",value:c.scope,required:true},{name:"rate",label:"Saatlik ücret (TL)",type:"number",step:"0.01",min:0,value:c.rate},{name:"weekly_limit",label:"Ortak haftalık saat sınırı",type:"number",step:"0.01",min:0,value:c.weekly_limit},{name:"expected_duration",label:"Beklenen süre",value:c.expected_duration,required:true},{name:"revision_terms",label:"Revizyon koşulları",type:"textarea",value:c.revision_terms,required:true},{name:"tracker_required",label:"Sabit işte masaüstü takip kullanılsın",type:"checkbox",value:c.tracker_required}].filter(field=>c.work_type==="hourly"?field.name!=="tracker_required":!["rate","weekly_limit"].includes(field.name)) as FieldSpec[]:[];
  return <Auth>
<State loading={contract.loading} error={contract.error} retry={contract.reload}>{c?<>
<Heading title={c.job_title||"Sözleşme çalışma alanı"} description={c.expected_duration} action={<Link href={`/messages/${c.conversation}`}>İş görüşmesini aç</Link>}/>
<div className="tabs">
<a href="#terms">Koşullar</a>
<a href={c.work_type==="hourly"?"#weekly":"#milestones"}>{c.work_type==="hourly"?"Haftalar":"Aşamalar"}</a>
<a href="#worklog">Çalışma günlüğü</a>
<a href="#support">İtiraz ve sonuç</a>
</div>
<Panel title="Kabul edilen koşullar">
<div id="terms"/>
<div className="meta">
<Status value={c.status}/>
<Status value={c.work_type}/>
<span>{c.team?"Takım sözleşmesi":"Bireysel iş"}</span>
</div>
<p className="long-text">{c.scope}</p>
<p>Revizyon: {c.revision_terms}</p>
<p>Takip: {c.tracker_required?"Zorunlu":"Tarafların tercihine bağlı"}. Kazanç iş bedelinden %10 platform komisyonuyla hesaplanır.</p>{c.work_type==="hourly"?<p>Saatlik ücret {money(c.rate)} · Ortak haftalık sınır {c.weekly_limit} saat.</p>:null}{c.members.length?<ul>{c.members.map(member=>
<li key={member.user}>{member.display_name||"İşe dahil öğrenci"} · {money(member.hourly_rate)}/saat</li>)}</ul>:null}{(employer||representative)&&c.status==="pending"?<Action path={`contracts/${id}/accept/`} label="Koşulları kabul et" disabled={c.stale_team_leader||c.accepted_by.includes(user?.id||"")} onSuccess={refresh} message="Kabulünüz kaydedildi. Diğer taraf kabul etmeden sözleşme aktif olmaz."/>:null}{employer&&c.status==="pending"&&c.team&&c.stale_team_leader?<div className="details"><Notice tone="warning">Takım lideri değiştiği için bekleyen sözleşme eski taraf/alıcı bilgileriyle kabul edilemez.</Notice><p>Yeni karşı taraf ve ödeme alıcısı: {c.current_team_leader?.display_name||"Yeni lider bilgisi alınamadı"}</p><p>Koşullar ve çalışan ücretleri korunur. Önceki kabuller sıfırlanır; iki taraf yeniden kabul eder. Bu işlem aktif bir işin lider değişikliği değildir.</p><TaskForm path={`contracts/${id}/reoffer/`} fields={[{name:"reason",label:"Yeni lidere yeniden teklif gerekçesi",type:"textarea",required:true}]} label="Mevcut koşulları yeni lidere yeniden teklif et" disabled={!c.current_team_leader?.display_name} message="Bekleyen sözleşme yeni liderle yeniden kabul sürecine alındı." onSuccess={refresh}/></div>:null}{c.status==="active"&&(employer||representative)?<details className="details">
<summary>Koşul değişikliği öner</summary>{c.team?<State loading={people.loading} error={people.error} retry={people.reload}><p className="muted">{people.items.length} öğrenci seçime hazır.</p></State>:null}
<TaskForm path={`contracts/${id}/changes/`} fields={changeFields} build={data=>({scope:value(data,"scope"),...(c.work_type==="hourly"?{rate:value(data,"rate"),weekly_limit:value(data,"weekly_limit")}:{tracker_required:data.has("tracker_required")}),expected_duration:value(data,"expected_duration"),revision_terms:value(data,"revision_terms"),...(newWorkers?{members:newWorkers.map(({user,hourly_rate})=>({user,hourly_rate}))}:{}),...(newStages.length?{milestones:[...c.milestones.map(stage=>({id:stage.id,title:stage.title,amount:stage.amount})),...newStages]}:{})})} label="Karşı tarafa değişiklik öner" message="Öneri gönderildi. Karşılıklı kabul edilene kadar mevcut şartlar geçerlidir." disabled={Boolean(c.team&&(people.loading||people.error))} onSuccess={()=>{setNewStages([]);setNewWorkers(null);refresh();}}>{c.team?<>
<WorkerEditor workers={newWorkers||c.members.map(member=>({user:member.user,hourly_rate:member.hourly_rate,display_name:member.display_name}))} setWorkers={setNewWorkers} people={people.items}/>

</>:null}{c.work_type==="fixed"?<>
<button type="button" className="button button-secondary" onClick={()=>setNewStages([{title:"",amount:""}])}>Yeni aşama öner</button>{newStages.length?<StageEditor stages={newStages} setStages={setNewStages}/>:null}</>:null}</TaskForm>
</details>:null}{c.changes?.map(change=><ContractChangeCard key={change.id} contract={c} change={change} people={people.items} inventoryReady={!peopleNeeded||(!people.loading&&!people.error)} userId={user?.id||""} canAccept={Boolean(employer||representative)} refresh={refresh}/>)}{c.leader_changes?.map(change=>
<article className="card" key={change.id}>
<h3>Lider değişikliği onayı</h3>
<p>{change.new_leader_name||"Yeni lider"} · Ödeme alıcısı: {change.payee_name||"Seçilen kişi"}</p>
<p>{change.reason}</p>
<Status value={change.status}/>{employer&&change.status==="pending"?<Action path={`leader-changes/${change.id}/approve/`} label="Lideri ve açıkça belirtilen ödeme alıcısını onayla" onSuccess={refresh}/>:null}</article>)}</Panel>{c.work_type==="fixed"?<Panel title="Aşamalar ve teslimler">
<div id="milestones"/>
<p className="muted">Her aşama önceden fonlanır. Onay veya 14 günlük sessizlikte ödeme serbest bırakılır; revizyon ve itiraz bu sayacı atlatmaz.</p>{c.milestones.map(stage=>
<MilestoneCard key={stage.id} milestone={stage} contract={c} employer={employer} worker={worker} refresh={refresh}/>)}</Panel>:<Panel title="Haftalık çalışma">
<div id="weekly"/>
<p className="muted">Ortak sınır üyelerin toplam süresine uygulanır. Hafta kapanırken bekleyen manuel kararlar ve yerel kayıtlar tamamlandıktan sonra 5 günlük inceleme başlar; manuel süre yalnız işverenin açık onayıyla ücretlendirilir.</p>{employer&&c.status==="active"?<TaskForm path={`contracts/${id}/weeks/`} fields={[{name:"starts_at",label:"Haftanın başlangıç tarihi",type:"date",help:"Boşsa sunucu mevcut Türkiye haftasını seçer."},{name:"remainder_choice",label:"Kullanılmayan fon",type:"select",required:true,options:[{value:"refund",label:"İade et"},{value:"rollover",label:"Sonraki haftaya aktar"}]}]} build={data=>({...(value(data,"starts_at")?{starts_at:new Date(`${value(data,"starts_at")}T00:00:00+03:00`).toISOString()}:{}),remainder_choice:value(data,"remainder_choice")})} label="Haftalık fonlama dönemi oluştur" onSuccess={refresh}/>:null}{log.data?.weeks.map(week=>
<WeekCard key={week.id} week={week} employer={employer} refresh={refresh}/>)}{worker&&c.status==="active"?<details className="details">
<summary>Manuel süre ekle</summary>
<TaskForm path={`contracts/${id}/manual-time/`} fields={[{name:"starts_at",label:"Başlangıç (cihaz saat dilimi)",type:"datetime-local",required:true},{name:"ends_at",label:"Bitiş (cihaz saat dilimi)",type:"datetime-local",required:true},{name:"memo",label:"Çalışma açıklaması",type:"textarea",required:true}]} build={data=>({starts_at:localISO(value(data,"starts_at")),ends_at:localISO(value(data,"ends_at")),memo:value(data,"memo")})} label="İşveren onayına gönder" message="Manuel süre onaya gönderildi; henüz kazanç değildir." onSuccess={refresh}/>
</details>:null}</Panel>}<div id="worklog"/>
<WorklogSection contract={c} data={log.data} loading={log.loading} error={log.error} reload={log.reload}/>
<Panel title="İtiraz, iptal ve tamamlanma">
<div id="support"/>{(employer||representative)?<>
<TaskForm path="disputes/" fields={[{name:"target",label:"İtiraz konusu",type:"select",required:true,options:[...c.milestones.map(stage=>({value:`milestone:${stage.id}`,label:stage.title})),...(log.data?.weeks||[]).map(week=>({value:`week:${week.id}`,label:`Hafta: ${date(week.starts_at)}`}))]},{name:"reason",label:"İtiraz gerekçesi",type:"textarea",required:true}]} build={data=>{const [kind,target]=value(data,"target").split(":");return{contract:id,[kind]:target,reason:value(data,"reason")};}} label="İtiraz aç" disabled={log.loading||Boolean(log.error)} message="İtiraz açıldı. İlgili ödeme çözüm süresince bekletilir." onSuccess={refresh}/>
<details className="details">
<summary>Sözleşmeyi iptal et</summary>
<p>Onaylanan işler ödenir; başlanmayan fonlar iade edilir. Yapılmış fakat onaylanmamış iş desteğe yönelir.</p>
<TaskForm path={`contracts/${id}/cancel/`} fields={[{name:"reason",label:"İptal gerekçesi",type:"textarea",required:true}]} label="Sözleşmeyi iptal et" onSuccess={refresh}/>
</details>
<Action path={`contracts/${id}/complete/`} label="Sözleşmeyi tamamla" onSuccess={refresh} message="Tamamlanma işlemi kaydedildi."/>
</>:null}</Panel>
<Panel title="Değerlendirmeler">
<State loading={ratings.loading} error={ratings.error} retry={ratings.reload}>{ratings.items.map(rating=>
<article className="card" key={rating.id}>
<strong>{rating.score}/5 · {rating.author_name||"Sözleşme tarafı"}</strong>
<p>{rating.comment}</p>
</article>)}<Pager {...ratings}/>
</State>{(employer||representative)?<TaskForm path={`contracts/${id}/ratings/`} fields={[{name:"score",label:"Puan",type:"select",required:true,options:[1,2,3,4,5].map(number=>({value:String(number),label:`${number} / 5`}))},{name:"comment",label:"Yorum",type:"textarea",required:true}]} build={data=>({score:Number(value(data,"score")),comment:value(data,"comment")})} label="Değerlendirme gönder" onSuccess={ratings.reload}/>:null}</Panel>
</>:null}</State>
</Auth>;
}
