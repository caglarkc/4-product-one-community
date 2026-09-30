"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useSession } from "@/components/session";
import { Action, Auth, Download, FilePicker, Heading, Notice, Panel, Pager, State, Status, TaskForm, tokens, usePaged, value, type FieldSpec } from "@/components/ui";
import { date, money, query, safeExternal, localDateTime } from "@/lib/api";
import { useResource, useCollection } from "@/lib/hooks";
import type { Application, Invitation, Job, PublicProfile, PublicTeam, Team } from "@/lib/types";
export function Boost({ type, id, onSuccess }: { type:"job"|"application"; id:string; onSuccess?:()=>void }) { const {config}=useSession();
  const policy=config?.credit_policy;
  const ready=policy?.boost_cost!=null && policy?.boost_hours!=null; return <details className="details">
<summary>Öne çıkar</summary>{ready ? <p>{String(policy.boost_cost)} kredi · {String(policy.boost_hours)} saat. İş bedeli değişmez.</p>:<Notice tone="warning">Öne çıkarma kredi maliyeti ve süresi henüz belirlenmedi.</Notice>}<Action path="boosts/" body={{target_type:type,target_id:id,duration_option:String(policy?.boost_hours||"")}} label="Öne çıkarmayı başlat" disabled={!ready} onSuccess={onSuccess} message="Öne çıkarma kaydedildi." />
</details>; }
function JobCard({job}:{job:Job}) { return <article className="card">
<h2>
<Link href={`/jobs/${job.id}`}>{job.title}</Link>
</h2>
<div className="meta">
<Status value={job.work_type}/>
<Status value={job.status}/>
<span>{money(job.budget)}</span>
<span>{job.expected_duration}</span>
</div>
<p>{job.description.slice(0,300)}{job.description.length>300?"…":""}</p>
<div className="meta">
<span>{job.owner_name}</span>
<span>{job.skills?.join(" · ")}</span>
<time>{date(job.created_at)}</time>
</div>
</article>; }
export function Jobs() { const [filters,setFilters]=useState({q:"",category:"",work_type:""});
  const {config}=useSession();
  const jobs=usePaged<Job>(query("jobs/",filters)); return <>
<Heading title="İlanları keşfet" description="Becerilerinize ve çalışma tercihinize uygun işleri inceleyin."/>
<Panel>
<form className="form-grid" onSubmit={event=>{event.preventDefault();
  const data=new FormData(event.currentTarget);setFilters({q:value(data,"q"),category:value(data,"category"),work_type:value(data,"work_type")});}}>
<label className="field">İlan ara<input name="q" type="search" defaultValue={filters.q}/>
</label>
<label className="field">Kategori<select name="category">
<option value="">Tümü</option>{config?.categories.map(item=>
<option key={item.id} value={item.id}>{item.name}</option>)}</select>
</label>
<label className="field">Çalışma türü<select name="work_type">
<option value="">Tümü</option>
<option value="fixed">Sabit ücret</option>
<option value="hourly">Saatlik</option>
</select>
</label>
<div className="actions">
<button className="button">İlanları ara</button>
</div>
</form>
</Panel>
<State loading={jobs.loading} error={jobs.error} empty={!jobs.items.length} retry={jobs.reload}>
<div className="card-list">{jobs.items.map(job=>
<JobCard key={job.id} job={job}/>)}</div>
<Pager {...jobs}/>
</State>
</>; }
export function People() { const [filter,setFilter]=useState({q:"",skill:""});
  const people=usePaged<PublicProfile>(query("profiles/",filter)); return <>
<Heading title="Öğrencileri keşfet" description="Öğrenci profillerini ve paylaşılan portföy bağlantılarını inceleyin."/>
<Panel>
<form className="form-grid" onSubmit={event=>{event.preventDefault();
  const data=new FormData(event.currentTarget);setFilter({q:value(data,"q"),skill:value(data,"skill")});}}>
<label className="field">Ad veya profil ara<input name="q" type="search"/>
</label>
<label className="field">Beceri<input name="skill"/>
</label>
<button className="button">Öğrencileri ara</button>
</form>
</Panel>
<State loading={people.loading} error={people.error} empty={!people.items.length} retry={people.reload}>
<div className="grid">{people.items.map(person=>
<Panel key={person.id} title={person.display_name}>
<p>{person.university} · {person.department}</p>
<p>{person.bio?.slice(0,220)}</p>
<p className="muted">{person.skills?.join(" · ")}</p>
<Link href={`/people/${person.id}`}>Profili incele</Link>
</Panel>)}</div>
<Pager {...people}/>
</State>
</>; }
export function PersonDetail() { const {id}=useParams<{id:string}>();
  const profile=useResource<PublicProfile>(`profiles/${id}/`); return <State loading={profile.loading} error={profile.error} retry={profile.reload}>{profile.data ? <>
<Heading title={profile.data.display_name||"Öğrenci profili"} description={`${profile.data.university||""} · ${profile.data.department||""}`}/>
<Panel>{safeExternal(profile.data.photo)?<img className="avatar" src={safeExternal(profile.data.photo)!} alt={`${profile.data.display_name||"Öğrenci"} profil fotoğrafı`}/>:null}<p className="long-text">{profile.data.bio}</p>
<p>{profile.data.skills?.join(" · ")}</p>
<p>Saatlik ücret: {money(profile.data.hourly_rate)}</p>
<h2>Portföy</h2>{profile.data.portfolio_links?.map((link,index)=>{const url=safeExternal(link.url);
  return url?<p key={index}>
<a href={url} target="_blank" rel="noopener noreferrer">{link.title}</a>
</p>:null;})}<p>
<Link href="/employer">Bir ilana davet et</Link>
</p>
</Panel>
</>:null}</State>; }
function jobFields(config: ReturnType<typeof useSession>["config"], job?:Job):FieldSpec[] { return [{name:"title",label:"İlan başlığı",required:true,value:job?.title},{name:"category",label:"Kategori",type:"select",required:true,value:job?.category,options:config?.categories.map(item=>({value:item.id,label:item.name}))},{name:"description",label:"İş açıklaması",type:"textarea",required:true,value:job?.description,help:"Beklenen sonucu ve işin kapsamını açıkça yazın."},{name:"skills",label:"Beceriler",value:job?.skills?.join(", "),help:"Virgülle ayırın."},{name:"work_type",label:"Çalışma türü",type:"select",required:true,value:job?.work_type,options:[{value:"fixed",label:"Sabit ücret"},{value:"hourly",label:"Saatlik"}]},{name:"budget",label:"Bütçe / saatlik ücret (TL)",type:"number",required:true,min:0,step:"0.01",value:job?.budget},{name:"expected_duration",label:"Beklenen süre",required:true,value:job?.expected_duration},{name:"deadline",label:"Son başvuru tarihi (cihaz saat dilimi)",type:"datetime-local",value:localDateTime(job?.deadline)}]; }
function jobPayload(data:FormData) { const deadline=value(data,"deadline");
  return {title:value(data,"title"),description:value(data,"description"),category:value(data,"category"),skills:tokens(value(data,"skills")),work_type:value(data,"work_type"),budget:value(data,"budget"),expected_duration:value(data,"expected_duration"),deadline:deadline?new Date(deadline).toISOString():null}; }
export function Employer() { const {user,config}=useSession();
  const jobs=usePaged<Job>(user?"jobs/?mine=true":null);
  const router=useRouter(); return <Auth>
<Heading title="İlanlarım" description="Bir ilandan birden fazla işe alım yapabilirsiniz. Her seçim için ayrı sözleşme kurulur."/>
<details className="panel">
<summary>Yeni ilan oluştur</summary>
<TaskForm<Job> path="jobs/" fields={jobFields(config)} build={data=>({...jobPayload(data),publish:false})} label="Taslak oluştur" disabled={!config||!config.categories.length} message="İlan taslağı oluşturuldu." onSuccess={job=>router.push(`/jobs/${job.id}`)}/>
</details>
<State loading={jobs.loading} error={jobs.error} empty={!jobs.items.length} retry={jobs.reload}>
<div className="card-list">{jobs.items.map(job=>
<JobCard key={job.id} job={job}/>)}</div>
<Pager {...jobs}/>
</State>
</Auth>; }
export function JobDetail() {
  const {id}=useParams<{id:string}>();
  const {user,config}=useSession();
  const job=useResource<Job>(`jobs/${id}/`);
  const owner=Boolean(user && job.data?.owner===user.id);
  const applications=usePaged<Application>(owner?`jobs/${id}/applications/`:null);
  const teams=useCollection<Team>(user?"teams/":null);
  const people=usePaged<PublicProfile>(owner?"profiles/":null);
  const publicTeams=usePaged<PublicTeam>(owner?"public-teams/":null);
  const policy=config?.credit_policy;
  const applyReady=policy?.apply_cost!=null;
  return <State loading={job.loading} error={job.error} retry={job.reload}>{job.data ? <>
<Heading title={job.data.title} description={job.data.owner_name}/>
<Panel>
<div className="meta">
<Status value={job.data.work_type}/>
<Status value={job.data.status}/>
<span>{money(job.data.budget)}</span>
<span>{job.data.expected_duration}</span>
</div>
<p className="long-text">{job.data.description}</p>
<p>{job.data.skills?.join(" · ")}</p>{job.data.deadline?<p>Son başvuru: {date(job.data.deadline)}</p>:null}{job.data.attachments?.map(file=>
<Download key={file.id} attachment={file}/>)}</Panel>{owner ? <>
<Panel title="İlan yönetimi">
<details>
<summary>İlanı düzenle</summary>
<TaskForm path={`jobs/${id}/`} method="PATCH" fields={jobFields(config,job.data)} build={jobPayload} label="Değişiklikleri kaydet" disabled={!config||!config.categories.length} onSuccess={job.reload}/>
<FilePicker scope={{job:id}} onChange={()=>job.reload()}/>
</details>{policy?.post_cost==null ? <Notice tone="warning">İlan yayınlama kredi maliyeti henüz belirlenmedi.</Notice>:<p>Yayınlama: {String(policy.post_cost)} kredi.</p>}<Action path={`jobs/${id}/publish/`} label="İlanı yayımla" disabled={job.data.status!=="draft"||policy?.post_cost==null} onSuccess={job.reload} message="İlan yayımlandı."/>
<Boost type="job" id={id} onSuccess={job.reload}/>
<details className="details">
<summary>İlanı iptal et</summary>
<p>İş anlaşması olmayan ilan için ilgili kredi iadeleri sunucu tarafından uygulanır. Aktif sözleşme ayrı işlemle iptal edilir.</p>
<TaskForm path={`jobs/${id}/cancel/`} fields={[{name:"reason",label:"İptal gerekçesi",type:"textarea",required:true}]} label="İlanı iptal et" onSuccess={job.reload}/>
</details>
</Panel>
<Panel title="Öğrenci veya takım davet et">
<State loading={people.loading||publicTeams.loading} error={people.error||publicTeams.error} retry={()=>{people.reload();publicTeams.reload();}}>
<TaskForm path={`jobs/${id}/invitations/`} fields={[{name:"student",label:"Öğrenci",type:"select",options:people.items.map(person=>({value:person.user||person.id,label:person.display_name||"Öğrenci"}))},{name:"team",label:"Takım",type:"select",options:publicTeams.items.map(team=>({value:team.id,label:team.name}))}]} build={data=>value(data,"team")?{team:value(data,"team")}:{student:value(data,"student")}} label="İlana davet et" message="Davet gönderildi. Görüşme mesajlarınızda açılır."/>
<Pager {...people}/>
<Pager {...publicTeams}/>
</State>
</Panel>
<Panel title="Başvurular">
<State loading={applications.loading} error={applications.error} empty={!applications.items.length} retry={applications.reload}>{applications.items.map(application=>
<article className="card" key={application.id}>
<h3>{application.team_name||application.student_name||"Öğrenci başvurusu"}</h3>
<div className="meta">
<Status value={application.status}/>
<span>{money(application.price)}</span>
<span>{application.duration}</span>
</div>
<p className="long-text">{application.cover_letter}</p>{safeExternal(application.sample_url)?<a href={safeExternal(application.sample_url)!} target="_blank" rel="noopener noreferrer">İş örneğini aç</a>:null}<div className="actions">
<Link href={`/contracts/new?job=${id}&application=${application.id}`}>Sözleşme hazırla</Link>
<Link href={`/messages/${application.conversation}`}>Görüşmeyi aç</Link>
<Action path={`applications/${application.id}/reject/`} label="Başvuruyu reddet" disabled={application.status!=="submitted"} onSuccess={applications.reload}/>
</div>
</article>)}<Pager {...applications}/>
</State>
</Panel>
</> : <Auth>
<Panel title="Bu işe teklif ver"><State loading={teams.loading} error={teams.error} retry={teams.reload}><p className="muted">Lideri olduğunuz bütün takımlar başvuru seçiminde yer alır.</p></State>{!applyReady?<Notice tone="warning">Başvuru kredi maliyeti henüz belirlenmedi. Davete verilen tekliften kredi kesilmez; uygunluk sunucuda kontrol edilir.</Notice>:<p>Standart başvuru {String(policy?.apply_cost)} kredi. Davet yanıtı kredi harcamaz.</p>}<TaskForm path={`jobs/${id}/applications/`} fields={[{name:"cover_letter",label:"Teklif mesajı",type:"textarea",required:true},{name:"price",label:job.data.work_type==="hourly"?"Saatlik ücret (TL)":"İş bedeli (TL)",type:"number",min:0,step:"0.01",required:true},{name:"duration",label:"Tahmini süre",required:true},{name:"sample_url",label:"İş örneği bağlantısı",type:"url"},{name:"team",label:"Başvuru adına",type:"select",help:"Boş bırakırsanız kendi adınıza başvurursunuz.",options:teams.items.filter(team=>team.leader===user?.id).map(team=>({value:team.id,label:team.name}))}]} build={data=>({cover_letter:value(data,"cover_letter"),price:value(data,"price"),duration:value(data,"duration"),sample_url:value(data,"sample_url")||null,team:value(data,"team")||null})} label="Teklif gönder" disabled={job.data.status!=="open"||teams.loading||Boolean(teams.error)||!user?.roles.includes("student")} message="Teklifiniz gönderildi; başvurularınızdan takip edebilirsiniz."/>
<details className="details">
<summary>İlanı şikâyet et</summary>
<TaskForm path={`jobs/${id}/report/`} fields={[{name:"reason",label:"Şikâyet gerekçesi",type:"textarea",required:true}]} label="Şikâyeti gönder" message="Şikâyet incelemeye gönderildi."/>
</details>
</Panel>
</Auth>}</>:null}</State>;
}
export function Applications() { const {user}=useSession();
  const applications=usePaged<Application>(user?"applications/":null);
  const invitations=usePaged<Invitation>(user?"invitations/":null);
  const teams=useCollection<Team>(user?"teams/":null);
  const leaderTeams=new Set(teams.items.filter(team=>team.leader===user?.id).map(team=>team.id));
  const ownApplication=(application:Application)=>application.team?(!teams.loading&&!teams.error&&leaderTeams.has(application.team)):application.student===user?.id;
  const ownInvitation=(invitation:Invitation)=>invitation.team?(!teams.loading&&!teams.error&&leaderTeams.has(invitation.team)):invitation.student===user?.id;
  return <Auth>
<Heading title="Başvurularım ve davetler" description="Seçim öncesi teklifinizi değiştirebilir veya geri çekebilirsiniz. Ret, geri çekme ve sürenin dolması kredi iadesi oluşturmaz."/>
<State loading={teams.loading} error={teams.error} retry={teams.reload}><p className="muted">Takım adına işlemleri yalnız güncel lider yapabilir.</p></State>
<Panel title="Davetler">
<State loading={invitations.loading} error={invitations.error} empty={!invitations.items.length} retry={invitations.reload}>{invitations.items.map(invitation=>
<article className="card" key={invitation.id}>
<h3>{invitation.job_title||"İlan daveti"}</h3>
<Status value={invitation.status}/>
<p>Davete verilen teklif başvuru kredisi harcamaz.</p>
<div className="actions">
<Link href={`/jobs/${invitation.job}`}>{ownInvitation(invitation)?"İlanı incele ve teklif ver":"İlanı incele"}</Link>{ownInvitation(invitation)&&invitation.conversation?<Link href={`/messages/${invitation.conversation}`}>Görüşme</Link>:null}{ownInvitation(invitation)&&invitation.status==="pending"?<Action path={`invitations/${invitation.id}/decline/`} label="Daveti reddet" onSuccess={invitations.reload}/>:null}
</div>
</article>)}<Pager {...invitations}/>
</State>
</Panel>
<Panel title="Gönderdiğim teklifler">
<State loading={applications.loading} error={applications.error} empty={!applications.items.length} retry={applications.reload}>{applications.items.map(application=>
<article className="card" key={application.id}>
<h3>
<Link href={`/jobs/${application.job}`}>{application.job_title||"İlanı aç"}</Link>
</h3>
<div className="meta">
<Status value={application.status}/>
<span>{money(application.price)}</span>
<span>{application.duration}</span>
</div>
<p className="long-text">{application.cover_letter}</p>
{ownApplication(application)?<Link href={`/messages/${application.conversation}`}>Görüşmeyi aç</Link>:null}{ownApplication(application)&&application.status==="submitted"?<>
<details className="details">
<summary>Teklifi düzenle</summary>
<TaskForm path={`applications/${application.id}/`} method="PATCH" fields={[{name:"cover_letter",label:"Teklif mesajı",type:"textarea",required:true,value:application.cover_letter},{name:"price",label:"Ücret (TL)",type:"number",step:"0.01",min:0,required:true,value:application.price},{name:"duration",label:"Tahmini süre",required:true,value:application.duration},{name:"sample_url",label:"İş örneği bağlantısı",type:"url",value:application.sample_url}]} label="Teklifi güncelle" onSuccess={applications.reload}/>
</details>
<Action path={`applications/${application.id}/withdraw/`} label="Teklifi geri çek" onSuccess={applications.reload}/>
<Boost type="application" id={application.id} onSuccess={applications.reload}/>
</>:null}</article>)}<Pager {...applications}/>
</State>
</Panel>
</Auth>; }
