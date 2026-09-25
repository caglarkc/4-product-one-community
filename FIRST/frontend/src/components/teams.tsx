'use client';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {useEffect,useRef,useState} from 'react';
import {api,ApiError} from '../lib/api';
import {labels,profileHref,type CommunityConfig} from '../lib/community';
import type {Project} from '../lib/projects';
import {organizationHref,teamRequestStatus,teamRoles,type Team,type TeamDetail,type TeamDraft,type TeamMine,type TeamPage,type TeamRequest} from '../lib/teams';
import {MultiChoice,Pagination} from './community-controls';
import {ProjectCard} from './project-card';
import {SessionPending,useSession} from './session-provider';
import {ActionLink,Alert,Button,Checkbox,Field,Input,PageHeading,Select,Surface} from './ui';

function errorText(error:unknown){return error instanceof ApiError?[error.message,...Object.values(error.errors||{}).flat()].join(' '):error instanceof Error?error.message:'İşlem tamamlanamadı.';}
function useAction(){
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');const lock=useRef(false),alive=useRef(true);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 async function run<T>(work:()=>Promise<T>,done:(value:T)=>void,success='İşlem kaydedildi.'){
  if(lock.current)return;lock.current=true;setBusy(true);setError('');setMessage('');
  try{const value=await work();if(alive.current){setMessage(success);done(value);}}catch(e){if(alive.current)setError(errorText(e));}finally{lock.current=false;if(alive.current)setBusy(false);}
 }
 return {busy,error,message,run};
}
function Feedback({error,message}:{error:string;message:string}){return <>{error&&<Alert tone="error" role="alert">{error}</Alert>}{message&&<Alert tone="success" role="status">{message}</Alert>}</>;}
function Retry({error,retry}:{error:string;retry:()=>void}){return <Alert tone="error" role="alert"><p>{error}</p><Button variant="secondary" onClick={retry}>Yeniden dene</Button></Alert>;}
function TeamCard({team,config}:{team:Team;config:CommunityConfig|null}){return <Surface className="repository-card"><div className="repository-card-kicker"><span>{team.recruiting?'Üye arıyor':'Başvurular kapalı'}</span>{team.my_role&&<span>{teamRoles[team.my_role]}</span>}</div><h2><Link href={`/ekipler/${team.id}`}>{team.name}</Link></h2><p className="repository-description">{team.description||'Henüz tanıtım eklenmedi.'}</p>{team.skills.length>0&&<p className="field-help">{labels(team.skills,config?.skills)}</p>}<div className="repository-card-footer"><Link href={profileHref(team.owner_username)}>@{team.owner_username}</Link><Link href={`/ekipler/${team.id}`}>Ekibi incele →</Link></div></Surface>;}
function TeamForm({initial,config,busy,onSave}:{initial?:TeamDraft;config:CommunityConfig;busy:boolean;onSave:(draft:TeamDraft)=>void}){
 const [draft,setDraft]=useState<TeamDraft>(initial||{name:'',description:'',recruiting:false,recruitment_text:'',skills:[],organization_url:''});
 return <form onSubmit={e=>{e.preventDefault();onSave(draft);}}><fieldset disabled={busy}>
 <Field id="team-name" label="Ekip adı"><Input id="team-name" required minLength={2} maxLength={100} value={draft.name} onChange={e=>setDraft({...draft,name:e.target.value})}/></Field>
 <Field id="team-description" label="Tanıtım"><textarea id="team-description" className="input" rows={3} maxLength={3000} value={draft.description} onChange={e=>setDraft({...draft,description:e.target.value})}/></Field>
 <Checkbox checked={draft.recruiting} onChange={e=>setDraft({...draft,recruiting:e.target.checked})}>Yeni üye başvurularını kabul et</Checkbox>
 <Field id="team-recruitment" label="Üye arama açıklaması"><textarea id="team-recruitment" className="input" rows={3} maxLength={2000} value={draft.recruitment_text} onChange={e=>setDraft({...draft,recruitment_text:e.target.value})}/></Field>
 <MultiChoice label="Ekip becerileri" options={config.skills} value={draft.skills} onChange={skills=>setDraft({...draft,skills})}/>
 <Field id="team-org" label="GitHub organizasyonu (isteğe bağlı)" help="https://github.com/organizasyon — yalnız tanıtım bağlantısıdır; üyelik veya erişim sağlamaz."><Input id="team-org" type="url" maxLength={300} placeholder="https://github.com/organizasyon" value={draft.organization_url} onChange={e=>setDraft({...draft,organization_url:e.target.value})}/></Field>
 <Button type="submit" loading={busy}>{initial?'Ekibi güncelle':'Ekibi oluştur'}</Button></fieldset></form>;
}
type RequestAction='accept'|'reject'|'withdraw'|'decline';
function RequestRow({row,username,manager,busy,onAction}:{row:TeamRequest;username?:string;manager:boolean;busy:boolean;onAction:(action:RequestAction)=>void}){
 const own=username===row.username;const pending=row.status==='pending';
 return <Surface className="project-panel"><p><Link href={`/ekipler/${row.team_id}`}>{row.team_name}</Link> · <Link href={profileHref(row.username)}>@{row.username}</Link> · {row.kind==='application'?'Başvuru':'Davet'} · {teamRequestStatus[row.status]}</p>{row.explanation&&<p className="project-text">{row.explanation}</p>}<div className="action-row">
 {pending&&((row.kind==='application'&&manager)||(row.kind==='invitation'&&own))&&<Button disabled={busy} onClick={()=>onAction('accept')}>Kabul et</Button>}
 {pending&&row.kind==='application'&&manager&&<Button variant="secondary" disabled={busy} onClick={()=>onAction('reject')}>Reddet</Button>}
 {pending&&row.kind==='invitation'&&own&&<Button variant="secondary" disabled={busy} onClick={()=>onAction('decline')}>Daveti reddet</Button>}
 {pending&&((row.kind==='application'&&own)||(row.kind==='invitation'&&manager))&&<Button variant="quiet" disabled={busy} onClick={()=>onAction('withdraw')}>Geri çek</Button>}
 </div></Surface>;
}

export function TeamsPage(){const {status,user}=useSession();if(status!=='ready')return <SessionPending/>;return <TeamsContent key={`${user?.id??'visitor'}:${user?.username}:${user?.email_verified}`}/>;}
function TeamsContent(){
 const {user}=useSession(),router=useRouter();const action=useAction();const [tab,setTab]=useState<'discover'|'mine'|'saved'|'create'>('discover');
 const [draft,setDraft]=useState(''),[q,setQ]=useState(''),[recruiting,setRecruiting]=useState(false),[page,setPage]=useState(1),[invitationsPage,setInvitationsPage]=useState(1),[retry,setRetry]=useState(0);
 const [data,setData]=useState<TeamPage|TeamMine|null>(null),[config,setConfig]=useState<CommunityConfig|null>(null),[error,setError]=useState('');
 useEffect(()=>{let active=true;setData(null);setError('');const query=new URLSearchParams({q,page:String(page),invitations_page:String(invitationsPage)});if(recruiting)query.set('recruiting','1');
 const request=tab==='create'?Promise.resolve(null):api<TeamPage|TeamMine>(tab==='mine'?'teams/mine':tab==='saved'?'teams/bookmarks':'teams',undefined,'GET',query);
 Promise.all([api<CommunityConfig>('community/config'),request]).then(([c,d])=>{if(active){setConfig(c);setData(d);}}).catch(e=>{if(active)setError(errorText(e));});return()=>{active=false;};},[tab,q,recruiting,page,invitationsPage,retry]);
 const refresh=()=>setRetry(v=>v+1);const canWrite=!!user?.email_verified;
 return <div className="community-page"><PageHeading eyebrow="FIRST / EKİPLER" title="Birlikte üretecek ekibini bul" description="Ekipler projelerden bağımsızdır. Ekip üyeliği GitHub erişimi sağlamaz."/>
 <nav className="action-row" aria-label="Ekip görünümleri">{([['discover','Keşfet'],['mine','Ekiplerim ve davetler'],['saved','Kaydedilenler'],['create','Ekip oluştur']] as const).filter(([key])=>user||key==='discover').map(([key,label])=><Button key={key} variant={tab===key?'primary':'quiet'} disabled={action.busy} aria-pressed={tab===key} onClick={()=>{setTab(key);setPage(1);}}>{label}</Button>)}{!user&&<ActionLink href="/giris" variant="secondary">Ekip kurmak için giriş yap</ActionLink>}</nav>
 <Feedback error={action.error} message={action.message}/>{user&&!canWrite&&<Alert>Ekip işlemleri için <Link href="/hesap">e-postanızı doğrulayın</Link>.</Alert>}
 {tab==='discover'&&<Surface className="project-panel"><form className="community-search" onSubmit={e=>{e.preventDefault();setQ(draft.trim());setPage(1);}}><Field id="team-search" label="Ekip ara"><Input id="team-search" type="search" maxLength={100} value={draft} onChange={e=>setDraft(e.target.value)}/></Field><Button type="submit">Ara</Button></form><Checkbox checked={recruiting} onChange={e=>{setRecruiting(e.target.checked);setPage(1);}}>Yalnız üye arayan ekipler</Checkbox></Surface>}
 {error?<Retry error={error} retry={refresh}/>:tab==='create'?config?<Surface className="project-panel"><h2>Yeni ekip</h2><TeamForm config={config} busy={action.busy||!canWrite} onSave={value=>void action.run(()=>api<{team:Team}>('teams',value),result=>router.push(`/ekipler/${result.team.id}`),'Ekip oluşturuldu.')}/></Surface>:<Alert role="status">Form yükleniyor…</Alert>:!data?<Alert role="status">Ekipler yükleniyor…</Alert>:<>
 {'count' in data&&<p aria-live="polite">{data.count} ekip</p>}<div className="repository-grid">{data.teams.map(team=><TeamCard key={team.id} team={team} config={config}/>)}</div>{!data.teams.length&&<Surface className="empty-state"><p>{tab==='mine'?'Henüz bir ekibe üye değilsiniz.':tab==='saved'?'Henüz ekip kaydetmediniz.':'Bu aramayla eşleşen ekip yok.'}</p></Surface>}
 {'count' in data&&<Pagination data={data} page={page} onChange={setPage}/>}
 {'team_pagination' in data&&<Pagination data={data.team_pagination} page={page} onChange={setPage}/>}
 {'invitations' in data&&<section><h2>Bekleyen davetler</h2>{!data.invitations.length&&<p>Bekleyen davetiniz yok.</p>}{data.invitations.map(row=><RequestRow key={row.id} row={row} username={user?.username} manager={false} busy={action.busy||!canWrite} onAction={value=>void action.run(()=>api(`teams/${row.team_id}/requests/${row.id}/action`,{action:value}),refresh)}/>)}<Pagination data={data.invitation_pagination} page={invitationsPage} onChange={setInvitationsPage}/></section>}
 </>}
 </div>;
}

export function TeamDetailPage({id}:{id:string}){const {status,user}=useSession();if(status!=='ready')return <SessionPending/>;return <TeamDetailContent key={`${id}:${user?.id??'visitor'}:${user?.username}:${user?.email_verified}`} id={id}/>;}
function TeamDetailContent({id}:{id:string}){
 const {user}=useSession(),router=useRouter();const action=useAction();const [data,setData]=useState<TeamDetail|null>(null),[config,setConfig]=useState<CommunityConfig|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 const [explanation,setExplanation]=useState(''),[invite,setInvite]=useState(''),[selectedProject,setSelectedProject]=useState(''),[confirmExit,setConfirmExit]=useState(false);
 const [membersPage,setMembersPage]=useState(1),[requestsPage,setRequestsPage]=useState(1),[projectsPage,setProjectsPage]=useState(1);
 const [ownProjects,setOwnProjects]=useState<Project[]|null>(null),[projectError,setProjectError]=useState(''),[projectRetry,setProjectRetry]=useState(0);
 useEffect(()=>{let active=true;setData(null);setError('');Promise.all([api<TeamDetail>(`teams/${id}`,undefined,'GET',new URLSearchParams({members_page:String(membersPage),requests_page:String(requestsPage),projects_page:String(projectsPage)})),api<CommunityConfig>('community/config')]).then(([d,c])=>{if(active){setData(d);setConfig(c);}}).catch(e=>{if(active)setError(errorText(e));});return()=>{active=false;};},[id,retry,membersPage,requestsPage,projectsPage]);
 const manager=data?.team.my_role==='owner'||data?.team.my_role==='admin';
 useEffect(()=>{let active=true;setOwnProjects(null);setProjectError('');if(manager&&user)api<{projects:Project[]}>('projects/mine').then(d=>{if(active)setOwnProjects(d.projects.filter(p=>p.is_active));}).catch(e=>{if(active)setProjectError(errorText(e));});return()=>{active=false;};},[manager,user?.id,projectRetry]);
 const refresh=()=>{setConfirmExit(false);setRetry(v=>v+1);};
 if(error)return <div className="community-page"><ActionLink href="/ekipler" variant="quiet">← Ekiplere dön</ActionLink><Retry error={error} retry={refresh}/></div>;
 if(!data||!config)return <Alert role="status">Ekip yükleniyor…</Alert>;
 const team=data.team,owner=team.my_role==='owner',canWrite=!!user?.email_verified,busy=action.busy||!canWrite;
 const org=organizationHref(team.organization_url);const pending=data.my_request?.status==='pending';
 const shownRequests=data.my_request&&!data.requests.some(r=>r.id===data.my_request?.id)?[data.my_request,...data.requests]:data.requests;
 const mutate=(path:string,body:unknown={},method='POST',message='İşlem kaydedildi.')=>void action.run(()=>api(`teams/${id}/${path}`,body,method),refresh,message);
 const initial:TeamDraft={name:team.name,description:team.description,recruiting:team.recruiting,recruitment_text:team.recruitment_text,skills:team.skills,organization_url:team.organization_url};
 return <div className="community-page"><ActionLink href="/ekipler" variant="quiet">← Ekiplere dön</ActionLink>
 <Surface className="project-panel"><PageHeading eyebrow="FIRST / EKİP" title={team.name} description={team.description||'Henüz tanıtım eklenmedi.'}/><div className="action-row"><span className={`connection-status${team.recruiting?' connection-status--connected':''}`}>{team.recruiting?'Yeni üyeler arıyor':'Başvurular kapalı'}</span>{team.my_role&&<span>{teamRoles[team.my_role]}</span>}<Link href={profileHref(team.owner_username)}>Sahip: @{team.owner_username}</Link>{user?<Button variant="secondary" disabled={busy} aria-pressed={team.saved} onClick={()=>mutate('bookmark',{},team.saved?'DELETE':'PUT',team.saved?'Ekip kaydedilenlerden çıkarıldı.':'Ekip kaydedildi.')}>{team.saved?'Kaydı kaldır':'Ekibi kaydet'}</Button>:<ActionLink href="/giris" variant="secondary">Giriş yap</ActionLink>}</div>
 {team.skills.length>0&&<p>{labels(team.skills,config.skills)}</p>}{org&&<p><a href={org} target="_blank" rel="noopener noreferrer">GitHub organizasyonu ↗</a><span className="field-help"> · Tanıtım bağlantısı; doğrulanmış üyelik değildir.</span></p>}<p className="field-help">Ekip üyeliği projelere veya GitHub repolarına erişim vermez.</p></Surface>
 <Feedback error={action.error} message={action.message}/>{user&&!canWrite&&<Alert>İşlem yapmak için <Link href="/hesap">e-postanızı doğrulayın</Link>.</Alert>}
 {team.recruitment_text&&<Surface className="project-panel"><h2>Aradığımız ekip arkadaşları</h2><p className="project-text">{team.recruitment_text}</p></Surface>}
 {manager&&<Surface className="project-panel"><details><summary>Ekip profilini ve üye arama ilanını düzenle</summary><TeamForm key={team.updated_at} initial={initial} config={config} busy={busy} onSave={value=>void action.run(()=>api(`teams/${id}`,value,'PATCH'),refresh,'Ekip güncellendi.')}/></details></Surface>}
 {!team.my_role&&!pending&&team.recruiting&&<Surface className="project-panel"><h2>Ekibe katıl</h2>{!user?<ActionLink href="/giris">Başvurmak için giriş yap</ActionLink>:<form onSubmit={e=>{e.preventDefault();mutate('apply',{explanation:explanation.trim()},'POST','Başvurunuz kaydedildi.');}}><fieldset disabled={busy}><Field id="team-application" label="Neden katılmak istiyorsunuz?"><textarea id="team-application" className="input" required minLength={10} maxLength={2000} rows={3} value={explanation} onChange={e=>setExplanation(e.target.value)}/></Field><Button type="submit" disabled={explanation.trim().length<10}>Başvuru gönder</Button></fieldset></form>}</Surface>}
 {manager&&<Surface className="project-panel"><h2>Bir kişiyi davet et</h2><form className="community-search" onSubmit={e=>{e.preventDefault();mutate('invitations',{username:invite.trim()},'POST','Davet kaydedildi.');}}><Field id="team-invite" label="FIRST kullanıcı adı"><Input id="team-invite" required minLength={3} maxLength={30} value={invite} disabled={busy} onChange={e=>setInvite(e.target.value)} autoComplete="off"/></Field><Button type="submit" disabled={busy}>Davet et</Button></form><p className="field-help">Kişinin davetlere açık olması gerekir. Davet, FIRST hesabında görünür.</p></Surface>}
 {(manager||shownRequests.length>0)&&<section><h2>{manager?'Bekleyen başvurular ve davetler':'Katılım durumunuz'}</h2>{!shownRequests.length&&<p>Bekleyen talep yok.</p>}{shownRequests.map(row=><RequestRow key={row.id} row={row} username={user?.username} manager={manager} busy={busy} onAction={value=>mutate(`requests/${row.id}/action`,{action:value})}/>)}<Pagination data={data.request_pagination} page={requestsPage} onChange={setRequestsPage}/></section>}
 <Surface className="project-panel"><h2>Üyeler</h2><ul className="team-member-list">{data.members.map(member=><li key={member.username}><div className="action-row"><Link href={profileHref(member.username)}>{member.full_name||member.username} <span className="field-help">@{member.username}</span></Link><span>{teamRoles[member.role]}</span>
 {owner&&member.role!=='owner'&&<><Button variant="quiet" disabled={busy} onClick={()=>mutate(`members/${encodeURIComponent(member.username)}/role`,{role:member.role==='admin'?'member':'admin'})}>{member.role==='admin'?'Üye yap':'Yönetici yap'}</Button><Button variant="secondary" disabled={busy} onClick={()=>{if(window.confirm(`Ekip sahipliğini @${member.username} kişisine devretmek istiyor musunuz? Siz yönetici olarak kalacaksınız.`))mutate('transfer',{username:member.username},'POST','Ekip sahipliği devredildi.');}}>Sahipliği devret</Button></>}
 {manager&&member.username!==user?.username&&member.role!=='owner'&&(owner||member.role==='member')&&<Button variant="danger" disabled={busy} onClick={()=>{if(window.confirm(`@${member.username} ekipten çıkarılsın mı?`))mutate(`members/${encodeURIComponent(member.username)}`,{},'DELETE','Üye ekipten çıkarıldı.');}}>Çıkar</Button>}
 </div></li>)}</ul><Pagination data={data.member_pagination} page={membersPage} onChange={setMembersPage}/></Surface>
 <section><h2>Bağlı projeler</h2><p className="field-help">Yalnız erişebildiğiniz aktif paylaşımlar görünür.</p>{!data.projects.length&&<p>Görüntülenebilen bağlı proje yok.</p>}<div className="repository-grid">{data.projects.map(project=><div key={project.id}><ProjectCard project={project}/>{(manager||project.owner_username===user?.username)&&<Button variant="quiet" disabled={busy} onClick={()=>{if(window.confirm('Projenin bu ekiple bağlantısı kaldırılsın mı?'))mutate(`projects/${project.id}`,{},'DELETE','Proje bağlantısı kaldırıldı.');}}>Ekipten ayır</Button>}</div>)}</div><Pagination data={data.project_pagination} page={projectsPage} onChange={setProjectsPage}/></section>
 {manager&&<Surface className="project-panel"><h2>Projeni ekibe bağla</h2><p className="field-help">Yalnız sahibi olduğunuz aktif projeleri bağlayabilirsiniz. Başka bir ekibe bağlı projenin önce o ekipten ayrılması gerekir.</p>{projectError?<Retry error={projectError} retry={()=>setProjectRetry(v=>v+1)}/>:!ownProjects?<p role="status">Projeleriniz yükleniyor…</p>:!ownProjects.length?<p>Aktif projeniz yok. <Link href="/projelerim/yeni">Proje paylaşın</Link>.</p>:<form className="community-search" onSubmit={e=>{e.preventDefault();mutate('projects',{project_id:selectedProject},'POST','Proje ekibe bağlandı.');}}><Field id="team-project" label="Projeniz"><Select id="team-project" required disabled={busy} value={selectedProject} onChange={e=>setSelectedProject(e.target.value)}><option value="">Proje seçin</option>{ownProjects.filter(p=>!data.projects.some(link=>link.id===p.id)).map(project=><option key={project.id} value={project.id}>{project.title}</option>)}</Select></Field><Button type="submit" disabled={busy||!selectedProject}>Ekibe bağla</Button></form>}</Surface>}
 {team.my_role&&<Surface className="project-panel"><details><summary>{owner?'Ekibi kapat':'Ekipten ayrıl'}</summary><p>{owner?'Ekibi kapatmak tüm üyelikleri kullanım dışı bırakır ve proje bağlantılarını kaldırır. GitHub projeleri silinmez. Ekibin sürmesi için önce sahipliği başka üyeye devredebilirsiniz.':'Ekipten ayrılınca ekip yönetimi ve üyeliğiniz sona erer. GitHub erişiminiz değişmez.'}</p><Checkbox checked={confirmExit} disabled={busy} onChange={e=>setConfirmExit(e.target.checked)}>{owner?'Ekibi kapatmak istediğimi onaylıyorum.':'Ekipten ayrılmak istediğimi onaylıyorum.'}</Checkbox><Button variant="danger" disabled={busy||!confirmExit} onClick={()=>void action.run(()=>api(owner?`teams/${id}`:`teams/${id}/leave`,{},owner?'DELETE':'POST'),()=>router.push('/ekipler'),owner?'Ekip kapatıldı.':'Ekipten ayrıldınız.')}>{owner?'Ekibi kapat':'Ekipten ayrıl'}</Button></details></Surface>}
 </div>;
}
