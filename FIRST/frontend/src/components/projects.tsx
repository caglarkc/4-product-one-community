'use client';
import {useEffect,useRef,useState} from 'react';
import {useRouter} from 'next/navigation';
import {api,User} from '../lib/api';
import {githubUrl,GitHubStatus,Project,ProjectConfig,Repository} from '../lib/projects';
import {ActionLink,Alert,Button,Checkbox,Field,Input,PageHeading,Select,Surface} from './ui';

function Failure({message}:{message:string}) {return <Alert role="alert" tone="error">{message}</Alert>;}
const categoryLabels:Record<string,string>={software:'Yazılım',design:'Tasarım',research:'Araştırma',documentation:'Dokümantasyon',other:'Diğer'};
function ProjectContent({project}:{project:Project}) {
 const link=!project.is_private && githubUrl(project.repository_url);
 return <><p className="eyebrow">{categoryLabels[project.category]||project.category} · {project.is_private?'Gizli repo':'Açık repo'}{!project.is_active?' · Arşivde':''}</p>
 <p className="project-text">{project.description}</p>{project.readme_excerpt && <><h2>README özeti</h2><p className="project-text">{project.readme_excerpt}</p></>}
 {link && <ActionLink href={link} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer" variant="secondary">Devamını oku — GitHub</ActionLink>}
 {project.is_private && <p className="field-help">Bu paylaşım yalnızca açıklamayı ve onaylanan kısa özeti içerir. Repo bağlantısı ve dosyalar paylaşılmaz.</p>}</>;
}
export function MyProjects(){
 const [projects,setProjects]=useState<Project[]|null>(null);const [error,setError]=useState('');const [needsLogin,setNeedsLogin]=useState(false);
 useEffect(()=>{let active=true;api<{projects:Project[]}>('projects/mine').then(data=>{if(active)setProjects(data.projects);}).catch(err=>{if(active){setError(err.message);setNeedsLogin(err.status===401||err.status===403);}});return()=>{active=false;};},[]);
 return <div className="account-page"><PageHeading title="Projelerim" eyebrow="FIRST / PROJELER" description="GitHub projelerinizi toplulukla paylaşın ve paylaşımlarınızı yönetin."/><ActionLink href="/projelerim/yeni">Proje paylaş</ActionLink>
 {error&&<Failure message={error}/>} {needsLogin&&<Alert><p>Projelerinizi görmek için giriş yapın.</p><ActionLink href="/giris">Giriş yap</ActionLink></Alert>} {!projects&&!error&&<Alert role="status">Projeler yükleniyor…</Alert>}
 {projects?.length===0&&<Surface><h2>Haydi, ilk reponu paylaş ve ekip arkadaşlarını bul</h2><p>GitHub hesabınızdan bir repo seçerek ilk paylaşımınızı hazırlayın.</p><ActionLink href="/projelerim/yeni">İlk projemi paylaş</ActionLink></Surface>}
 <div className="project-grid">{projects?.map(project=><Surface key={project.id}><h2><a href={`/projeler/${project.id}`}>{project.title}</a></h2><ProjectContent project={project}/><p><ActionLink variant="quiet" href={`/projelerim/${project.id}/duzenle`}>Paylaşımı düzenle</ActionLink></p></Surface>)}</div></div>;
}
export function ProjectDetail({id}:{id:string}){
 const [project,setProject]=useState<Project|null>(null);const [error,setError]=useState('');
 useEffect(()=>{let active=true;api<{project:Project}>(`projects/${id}`).then(data=>{if(active)setProject(data.project);}).catch(err=>{if(active)setError(err.message);});return()=>{active=false;};},[id]);
 return <div className="account-page">{error?<Failure message={error}/>:project?<Surface><PageHeading title={project.title} eyebrow="FIRST / PROJE"/><ProjectContent project={project}/></Surface>:<Alert role="status">Proje yükleniyor…</Alert>}</div>;
}
export function ProjectEditor({id}:{id?:string}){
 const router=useRouter();const lock=useRef(false);const [user,setUser]=useState<User|null>();const [config,setConfig]=useState<ProjectConfig>();const [status,setStatus]=useState<GitHubStatus>();
 const [repositories,setRepositories]=useState<Repository[]>([]);const [selected,setSelected]=useState('');const [preview,setPreview]=useState<{repository:Repository;readme_excerpt:string}>();const [existing,setExisting]=useState<Project>();
 const [title,setTitle]=useState('');const [category,setCategory]=useState('');const [description,setDescription]=useState('');const [includeExcerpt,setIncludeExcerpt]=useState(true);const [confirmed,setConfirmed]=useState(false);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [ready,setReady]=useState(false);
 useEffect(()=>{let active=true;(async()=>{try{
   const session=await api<{user:User|null}>('me');if(!active)return;if(!id&&new URLSearchParams(window.location.search).get('github')==='failed')setError('GitHub repo bağlantısı tamamlanamadı. Yeniden deneyin.');setUser(session.user);if(!session.user){setReady(true);return;}
   const settings=await api<ProjectConfig>('projects/config');if(!active)return;setConfig(settings);
   if(id){const data=await api<{projects:Project[]}>('projects/mine');if(!active)return;const owned=data.projects.find(item=>item.id===id);if(!owned)throw new Error('Düzenleyebileceğiniz paylaşım bulunamadı.');setExisting(owned);setTitle(owned.title);setCategory(owned.category);setDescription(owned.description);}
   else {const data=await api<GitHubStatus>('projects/github/status');if(!active)return;setStatus(data);if(data.connected){const repos=await api<{repositories:Repository[]}>('projects/github/repositories');if(active)setRepositories(repos.repositories);}}
 }catch(err){if(active)setError((err as Error).message);}finally{if(active)setReady(true);}})();return()=>{active=false;};},[id]);
 async function perform(action:()=>Promise<void>){if(lock.current)return;lock.current=true;setBusy(true);setError('');try{await action();}catch(err){setError((err as Error).message);}finally{lock.current=false;setBusy(false);}}
 const eligible=!!user?.email_verified&&!!user?.providers.includes('github');
 return <div className="account-page"><PageHeading title={id?'Paylaşımı düzenle':'Proje paylaş'} eyebrow="FIRST / PROJELER"/><p><ActionLink variant="quiet" href="/projelerim">Projelerime dön</ActionLink></p>
 {error&&<Failure message={error}/>} {!ready&&<Alert role="status">Paylaşım bilgileri yükleniyor…</Alert>}
 {ready&&user===null&&<Alert><p>Proje paylaşmak için giriş yapın.</p><ActionLink href="/giris">Giriş yap</ActionLink></Alert>}
 {user&&!eligible&&<Alert><p>Paylaşım için e-posta adresiniz doğrulanmış ve GitHub hesabınız bağlı olmalıdır. Telefon doğrulaması gerekmez.</p><ActionLink href="/hesap">Hesabımı düzenle</ActionLink></Alert>}
 {ready&&user&&!id&&eligible&&<Surface><h2>1. GitHub reposunu seçin</h2>
 {!status?.enabled||!config?.github_app_enabled?<Alert>GitHub repo bağlantısı henüz kullanıma hazır değil. Daha sonra tekrar deneyin.</Alert>:<>
 <p>GitHub uygulamasına yalnızca seçtiğiniz repolar için erişim verirsiniz. Seçebileceğiniz repolarda yönetici yetkiniz bulunmalıdır.</p>
 {status.connected ? <ActionLink href="/github-kurulum?next=%2Fprojelerim%2Fyeni&manage=1" variant="quiet">Repo izinlerini yönet</ActionLink> : <ActionLink href="/github-kurulum?next=%2Fprojelerim%2Fyeni">GitHub repo izinlerini tamamla</ActionLink>}
 {status.connected&&<><Button variant="quiet" disabled={busy} onClick={()=>perform(async()=>{const data=await api<{repositories:Repository[]}>('projects/github/repositories');setRepositories(data.repositories);setPreview(undefined);setSelected('');setConfirmed(false);})}>Repo listesini yenile</Button>
 {repositories.length===0?<p>Seçilebilir repo bulunamadı. Repo izinlerini yöneterek bir repo seçebilir, ardından listeyi yenileyebilirsiniz.</p>:<Field id="repository" label="GitHub reposu"><Select id="repository" value={selected} disabled={busy} onChange={event=>{setSelected(event.target.value);setPreview(undefined);setConfirmed(false);}}><option value="">Bir repo seçin</option>{repositories.map(repo=><option key={`${repo.installation_id}:${repo.id}`} value={`${repo.installation_id}:${repo.id}`}>{repo.full_name} — {repo.private?'Gizli':'Açık'}</option>)}</Select></Field>}
 <Button variant="secondary" disabled={!selected||busy} onClick={()=>perform(async()=>{const repo=repositories.find(item=>`${item.installation_id}:${item.id}`===selected);if(!repo)return;const data=await api<{repository:Repository;readme_excerpt:string}>('projects/github/preview',{installation_id:repo.installation_id,repository_id:repo.id});setPreview(data);setConfirmed(false);if(!title)setTitle(data.repository.name);})}>Paylaşımı hazırla</Button></>}
 </>}</Surface>}
 {user&&config&&(existing||preview)&&<Surface><h2>{id?'Paylaşım bilgileri':'2. Paylaşımı gözden geçirin'}</h2><form onSubmit={event=>{event.preventDefault();if(!eligible||(!id&&!confirmed))return;perform(async()=>{const body=id?{title,category,description}:{title,category,description,installation_id:preview!.repository.installation_id,repository_id:preview!.repository.id,readme_excerpt:includeExcerpt?preview!.readme_excerpt:''};const data=await api<{project:Project}>(id?`projects/${id}`:'projects',body,id?'PATCH':'POST');router.push(`/projeler/${data.project.id}`);});}}>
 <Field id="project-title" label="Proje başlığı"><Input id="project-title" value={title} onChange={e=>{setTitle(e.target.value);setConfirmed(false);}} required maxLength={200}/></Field>
 <Field id="project-category" label="Kategori"><Select id="project-category" value={category} onChange={e=>{setCategory(e.target.value);setConfirmed(false);}} required><option value="">Kategori seçin</option>{config.categories.map(item=><option key={item.value} value={item.value}>{item.label}</option>)}</Select></Field>
 <Field id="project-description" label="Açıklama (isteğe bağlı)"><textarea className="input project-textarea" id="project-description" value={description} onChange={e=>{setDescription(e.target.value);setConfirmed(false);}} maxLength={5000} rows={7}/></Field>
 {!id&&preview&&<><Alert><p>{preview.repository.private?'Gizli repo: Repo bağlantısı ve dosyalar yayımlanmaz. Aşağıdaki başlık, kategori, açıklama ve seçerseniz README özeti herkes tarafından görülebilir.':'Açık repo: Başlık, kategori, açıklama, seçerseniz README özeti ve GitHub bağlantısı herkes tarafından görülebilir.'}</p></Alert>
 {preview.readme_excerpt?<><Checkbox checked={includeExcerpt} onChange={e=>{setIncludeExcerpt(e.target.checked);setConfirmed(false);}}>README özetini paylaş</Checkbox><p className="project-text">{preview.readme_excerpt}</p></>:<p>Paylaşılabilecek README özeti bulunamadı.</p>}
 <Checkbox checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}>Gösterilen bilgileri gözden geçirdim ve toplulukla paylaşılmasını onaylıyorum.</Checkbox></>}
 <Button type="submit" loading={busy} disabled={!eligible||(!id&&!confirmed)}>{id?'Değişiklikleri kaydet':'Projeyi paylaş'}</Button></form>
 {existing&&<Button variant={existing.is_active?'danger':'secondary'} disabled={busy||(!existing.is_active&&!eligible)} onClick={()=>perform(async()=>{const data=await api<{project:Project}>(`projects/${id}`,{is_active:!existing.is_active},'PATCH');setExisting(data.project);})}>{existing.is_active?'Paylaşımı arşivle':'Paylaşımı yeniden aç'}</Button>}
 </Surface>}</div>;
}
