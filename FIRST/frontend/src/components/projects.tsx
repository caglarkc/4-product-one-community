'use client';
import {useEffect,useRef,useState} from 'react';
import {useRouter} from 'next/navigation';
import {api,ApiError} from '../lib/api';
import {RequireSession, SessionPending, useSession} from './session-provider';
import {githubUrl,GitHubStatus,Project,ProjectConfig,Repository} from '../lib/projects';
import {ActionLink,Alert,Button,Checkbox,Field,Input,PageHeading,Select,Surface} from './ui';

function ProjectContent({project}:{project:Project}) {
 const link=!project.is_private && githubUrl(project.repository_url);
 return <><div className="project-sharing"><span className={`connection-status${project.is_active?' connection-status--connected':''}`}>{project.is_active?'Paylaşım aktif':'Arşivde'}</span><span>{project.is_private?'Gizli repo':'Açık repo'}</span></div>
 <dl className="project-taxonomy"><div><dt>Üst kategori</dt><dd>{project.category_label || 'Belirtilmedi'}</dd></div><div><dt>Alt kategori</dt><dd>{project.subcategory_label || 'Belirtilmedi'}</dd></div><div><dt>Proje durumu</dt><dd>{project.stage_label || 'Belirtilmedi'}</dd></div></dl>
 <p className="project-text">{project.description}</p>{project.readme_excerpt && <><h2>README özeti</h2><p className="project-text">{project.readme_excerpt}</p></>}
 {link && <ActionLink href={link} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer" variant="secondary">Devamını oku — GitHub</ActionLink>}
 {project.is_private && <p className="field-help">Bu paylaşım yalnızca açıklamayı ve onaylanan kısa özeti içerir. Repo bağlantısı ve dosyalar paylaşılmaz.</p>}</>;
}
export function MyProjects() {return <RequireSession><MyProjectsContent/></RequireSession>;}
function MyProjectsContent(){
 const [projects,setProjects]=useState<Project[]|null>(null);const [error,setError]=useState('');const [retry,setRetry]=useState(0);
 useEffect(()=>{let active=true;setError('');api<{projects:Project[]}>('projects/mine').then(data=>{if(active)setProjects(data.projects);}).catch(err=>{if(active)setError(err.message);});return()=>{active=false;};},[retry]);
 return <div className="account-page project-page"><div className="page-toolbar"><PageHeading title="Projelerim" eyebrow="FIRST / PROJELER" description="Paylaşımlarınızı görüntüleyin, güncelleyin ve yeni projelerinizi tanıtın."/><ActionLink href="/projelerim/yeni">Proje paylaş</ActionLink></div>
 {error&&<Alert role="alert" tone="error"><p>{error}</p><Button variant="secondary" onClick={()=>setRetry(value=>value+1)}>Yeniden dene</Button></Alert>}{!projects&&!error&&<Alert role="status">Projeleriniz yükleniyor…</Alert>}
 {projects?.length===0&&<Surface className="empty-state"><p className="eyebrow">İLK PAYLAŞIMINIZ</p><h2>Projelerinizi burada bir araya getirin.</h2><p>Henüz bir proje paylaşmadınız. GitHub hesabınızdan bir repo seçerek ilk paylaşımınızı hazırlayabilirsiniz.</p><ActionLink href="/projelerim/yeni">İlk projemi paylaş</ActionLink></Surface>}
 <div className="project-grid">{projects?.map(project=><Surface key={project.id} className="project-card"><div className="project-card-heading"><h2><a href={`/projeler/${project.id}`}>{project.title}</a></h2></div><ProjectContent project={project}/><div className="action-row"><ActionLink variant="secondary" href={`/projeler/${project.id}`}>Paylaşımı görüntüle</ActionLink><ActionLink variant="quiet" href={`/projelerim/${project.id}/duzenle`}>Düzenle</ActionLink></div></Surface>)}</div></div>;
}
export function ProjectDetail({id}:{id:string}) {
 const {status,user}=useSession();
 if(status === 'loading') return <SessionPending/>;
 return <ProjectDetailContent key={`${id}:${status}:${user?.id ?? 'visitor'}`} id={id}/>;
}
function ProjectDetailContent({id}:{id:string}){
 const {user}=useSession();
 const [project,setProject]=useState<Project|null>(null);const [error,setError]=useState('');const [retry,setRetry]=useState(0);
 useEffect(()=>{let active=true;setProject(null);setError('');api<{project:Project}>(`projects/${id}`).then(data=>{if(active)setProject(data.project);}).catch(err=>{if(active)setError(err.message);});return()=>{active=false;};},[id,retry]);
 return <div className="account-page project-page"><div className="back-link"><ActionLink variant="quiet" href={user?'/projelerim':'/'}>{user?'Projelerime dön':'Ana sayfaya dön'}</ActionLink></div>{error?<Alert role="alert" tone="error"><p>{error}</p><Button variant="secondary" onClick={()=>setRetry(value=>value+1)}>Yeniden dene</Button></Alert>:project?<Surface className="project-detail"><PageHeading title={project.title} eyebrow="FIRST / PROJE"/><ProjectContent project={project}/></Surface>:<Alert role="status">Proje yükleniyor…</Alert>}</div>;
}
export function ProjectEditor({id}:{id?:string}) {return <RequireSession><ProjectEditorContent key={id || 'new'} id={id}/></RequireSession>;}
function ProjectEditorContent({id}:{id?:string}){
 const router=useRouter();const lock=useRef(false);const {user}=useSession();const [retry,setRetry]=useState(0);const [config,setConfig]=useState<ProjectConfig>();const [status,setStatus]=useState<GitHubStatus>();
 const [repositories,setRepositories]=useState<Repository[]>([]);const [selected,setSelected]=useState('');const [preview,setPreview]=useState<{repository:Repository;readme_excerpt:string}>();const [existing,setExisting]=useState<Project>();
 const [title,setTitle]=useState('');const [category,setCategory]=useState('');const [subcategory,setSubcategory]=useState('');const [stage,setStage]=useState('');const [fieldErrors,setFieldErrors]=useState<Record<string,string[]>>({});const [description,setDescription]=useState('');const [includeExcerpt,setIncludeExcerpt]=useState(true);const [confirmed,setConfirmed]=useState(false);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [ready,setReady]=useState(false);
 useEffect(()=>{let active=true;setReady(false);setError('');(async()=>{try{
   if(!id&&new URLSearchParams(window.location.search).get('github')==='failed')setError('GitHub repo bağlantısı tamamlanamadı. Yeniden deneyin.');
   const settings=await api<ProjectConfig>('projects/config');if(!active)return;setConfig(settings);
   if(id){const data=await api<{projects:Project[]}>('projects/mine');if(!active)return;const owned=data.projects.find(item=>item.id===id);if(!owned)throw new Error('Düzenleyebileceğiniz paylaşım bulunamadı.');setExisting(owned);setTitle(owned.title);setCategory(owned.category);setSubcategory(owned.subcategory || '');setStage(owned.stage || '');setDescription(owned.description);}
   else {const data=await api<GitHubStatus>('projects/github/status');if(!active)return;setStatus(data);if(data.connected){const repos=await api<{repositories:Repository[]}>('projects/github/repositories');if(active)setRepositories(repos.repositories);}}
 }catch(err){if(active)setError((err as Error).message);}finally{if(active)setReady(true);}})();return()=>{active=false;};},[id,retry]);
 async function perform(action:()=>Promise<void>){if(lock.current)return;lock.current=true;setBusy(true);setError('');setFieldErrors({});try{await action();}catch(err){setError((err as Error).message);if(err instanceof ApiError)setFieldErrors(err.errors);}finally{lock.current=false;setBusy(false);}}
 const categories=Array.isArray(config?.categories)?config.categories:[];
 const stages=Array.isArray(config?.stages)?config.stages:[];
 const taxonomyReady=categories.length>0&&stages.length>0&&categories.every(item=>Array.isArray(item.subcategories)&&item.subcategories.length>0);
 const selectedCategory=categories.find(item=>item.value===category);
 const subcategories=selectedCategory?.subcategories || [];
 const selectedStage=stages.find(item=>item.value===stage);
 const taxonomySelected=taxonomyReady&&!!selectedCategory&&subcategories.some(item=>item.value===subcategory)&&!!selectedStage;
 const fieldError=(name:string)=>fieldErrors[name]?.join(' ');
 const fieldA11y=(name:string,help=false)=>({'aria-invalid':!!fieldError(name),'aria-describedby':[help?`project-${name}-help`:'',fieldError(name)?`project-${name}-error`:''].filter(Boolean).join(' ')||undefined});
 const eligible=!!user?.email_verified&&!!user?.providers.includes('github');
 return <div className="account-page project-page"><PageHeading description={id?'Paylaşımınızın bilgilerini güncelleyin veya görünürlüğünü yönetin.':'Önce GitHub reponuzu seçin, ardından paylaşılacak bilgileri gözden geçirin.'} title={id?'Paylaşımı düzenle':'Proje paylaş'} eyebrow="FIRST / PROJELER"/><p><ActionLink variant="quiet" href="/projelerim">Projelerime dön</ActionLink></p>
 {error&&<Alert role="alert" tone="error"><p>{error}</p>{Object.entries(fieldErrors).filter(([name])=>!['title','category','subcategory','stage','description'].includes(name)).map(([name,messages])=><p key={name}>{messages.join(' ')}</p>)}{ready&&!busy&&Object.keys(fieldErrors).length===0&&<Button variant="secondary" onClick={()=>setRetry(value=>value+1)}>Yeniden dene</Button>}</Alert>} {!ready&&<Alert role="status">Paylaşım bilgileri yükleniyor…</Alert>}
 {ready&&config&&!taxonomyReady&&<Alert role="status"><p>Proje kategorileri ve durumları hazırlanıyor. Seçenekler hazır olduğunda paylaşımınızı kaydedebilirsiniz.</p><Button variant="secondary" disabled={busy} onClick={()=>perform(async()=>{setConfig(await api<ProjectConfig>('projects/config'));})}>Seçenekleri yeniden yükle</Button></Alert>}
 {ready&&user===null&&<Alert><p>Proje paylaşmak için giriş yapın.</p><ActionLink href="/giris">Giriş yap</ActionLink></Alert>}
 {user&&!eligible&&<Alert><p>Paylaşım için e-posta adresiniz doğrulanmış ve GitHub hesabınız bağlı olmalıdır. Bağlantınızı ve e-posta doğrulamanızı Hesabım bölümünden tamamlayabilirsiniz.</p><ActionLink href="/hesap">Hesabımı düzenle</ActionLink></Alert>}
 {ready&&user&&!id&&eligible&&<Surface className="project-panel"><h2>1. GitHub reposunu seçin</h2>
 {!status?.enabled||!config?.github_app_enabled?<Alert>GitHub repo bağlantısı henüz kullanıma hazır değil. Daha sonra tekrar deneyin.</Alert>:<>
 <p>GitHub uygulamasına yalnızca seçtiğiniz repolar için erişim verirsiniz. Seçebileceğiniz repolarda yönetici yetkiniz bulunmalıdır.</p>
 {status.connected ? <ActionLink href="/github-kurulum?next=%2Fprojelerim%2Fyeni&manage=1" variant="quiet">Repo izinlerini yönet</ActionLink> : <ActionLink href="/github-kurulum?next=%2Fprojelerim%2Fyeni">GitHub repo izinlerini tamamla</ActionLink>}
 {status.connected&&<><Button variant="quiet" disabled={busy} onClick={()=>perform(async()=>{const data=await api<{repositories:Repository[]}>('projects/github/repositories');setRepositories(data.repositories);setPreview(undefined);setSelected('');setConfirmed(false);})}>Repo listesini yenile</Button>
 {repositories.length===0?<p>Seçilebilir repo bulunamadı. Repo izinlerini yöneterek bir repo seçebilir, ardından listeyi yenileyebilirsiniz.</p>:<Field id="repository" label="GitHub reposu"><Select id="repository" value={selected} disabled={busy} onChange={event=>{setSelected(event.target.value);setPreview(undefined);setConfirmed(false);}}><option value="">Bir repo seçin</option>{repositories.map(repo=><option key={`${repo.installation_id}:${repo.id}`} value={`${repo.installation_id}:${repo.id}`}>{repo.full_name} — {repo.private?'Gizli':'Açık'}</option>)}</Select></Field>}
 <Button variant="secondary" disabled={!selected||busy} onClick={()=>perform(async()=>{const repo=repositories.find(item=>`${item.installation_id}:${item.id}`===selected);if(!repo)return;const data=await api<{repository:Repository;readme_excerpt:string}>('projects/github/preview',{installation_id:repo.installation_id,repository_id:repo.id});setPreview(data);setConfirmed(false);if(!title)setTitle(data.repository.name);})}>Paylaşımı hazırla</Button></>}
 </>}</Surface>}
 {user&&config&&(existing||preview)&&<Surface className="project-panel"><h2>{id?'Paylaşım bilgileri':'2. Paylaşımı gözden geçirin'}</h2><form aria-busy={busy} onSubmit={event=>{event.preventDefault();if(!eligible||!taxonomySelected||(!id&&!confirmed))return;perform(async()=>{const body=id?{title,category,subcategory,stage,description}:{title,category,subcategory,stage,description,installation_id:preview!.repository.installation_id,repository_id:preview!.repository.id,readme_excerpt:includeExcerpt?preview!.readme_excerpt:''};const data=await api<{project:Project}>(id?`projects/${id}`:'projects',body,id?'PATCH':'POST');router.push(`/projeler/${data.project.id}`);});}}><fieldset disabled={busy}>
 <Field id="project-title" label="Proje başlığı" error={fieldError('title')}><Input id="project-title" {...fieldA11y('title')} value={title} onChange={e=>{setTitle(e.target.value);setConfirmed(false);}} required maxLength={200}/></Field>
 <Field id="project-category" label="Üst kategori" help="Projenizin ana çıktısının türünü seçin." error={fieldError('category')}><Select id="project-category" {...fieldA11y('category',true)} value={selectedCategory?category:''} onChange={e=>{setCategory(e.target.value);setSubcategory('');setConfirmed(false);}} required disabled={!taxonomyReady}><option value="">Üst kategori seçin</option>{categories.map(item=><option key={item.value} value={item.value}>{item.label}</option>)}</Select></Field>
 <Field id="project-subcategory" label="Alt kategori" help={selectedCategory?'Bu proje türünün hizmet ettiği ana amacı seçin.':'Alt kategorileri görmek için önce üst kategori seçin.'} error={fieldError('subcategory')}><Select id="project-subcategory" {...fieldA11y('subcategory',true)} value={subcategories.some(item=>item.value===subcategory)?subcategory:''} onChange={e=>{setSubcategory(e.target.value);setConfirmed(false);}} required disabled={!taxonomyReady||!selectedCategory}><option value="">Alt kategori seçin</option>{subcategories.map(item=><option key={item.value} value={item.value}>{item.label}</option>)}</Select></Field>
 <Field id="project-stage" label="Proje durumu" help={selectedStage?.description || 'Projenizin bugün bulunduğu aşamayı seçin. Bu bilgi proje sahibinin beyanıdır.'} error={fieldError('stage')}><Select id="project-stage" {...fieldA11y('stage',true)} value={selectedStage?stage:''} onChange={e=>{setStage(e.target.value);setConfirmed(false);}} required disabled={!taxonomyReady}><option value="">Proje durumu seçin</option>{stages.map(item=><option key={item.value} value={item.value}>{item.label}</option>)}</Select></Field>
 <Field id="project-description" label="Açıklama (isteğe bağlı)" error={fieldError('description')}><textarea {...fieldA11y('description')} className="input project-textarea" id="project-description" value={description} onChange={e=>{setDescription(e.target.value);setConfirmed(false);}} maxLength={5000} rows={7}/></Field>
 {!id&&preview&&<><Alert><p>{preview.repository.private?'Gizli repo: Repo bağlantısı ve dosyalar yayımlanmaz. Aşağıdaki başlık, üst ve alt kategori, proje durumu, açıklama ve seçerseniz README özeti herkes tarafından görülebilir.':'Açık repo: Başlık, üst ve alt kategori, proje durumu, açıklama, seçerseniz README özeti ve GitHub bağlantısı herkes tarafından görülebilir.'}</p></Alert>
 {preview.readme_excerpt?<><Checkbox checked={includeExcerpt} onChange={e=>{setIncludeExcerpt(e.target.checked);setConfirmed(false);}}>README özetini paylaş</Checkbox><p className="project-text">{preview.readme_excerpt}</p></>:<p>Paylaşılabilecek README özeti bulunamadı.</p>}
 <Checkbox checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}>Gösterilen bilgileri gözden geçirdim ve toplulukla paylaşılmasını onaylıyorum.</Checkbox></>}
 <Button type="submit" loading={busy} disabled={!eligible||!taxonomySelected||(!id&&!confirmed)}>{id?'Değişiklikleri kaydet':'Projeyi paylaş'}</Button></fieldset></form>
 {existing&&<Button variant={existing.is_active?'danger':'secondary'} disabled={busy||(!existing.is_active&&!eligible)} onClick={()=>perform(async()=>{const data=await api<{project:Project}>(`projects/${id}`,{is_active:!existing.is_active},'PATCH');setExisting(data.project);})}>{existing.is_active?'Paylaşımı arşivle':'Paylaşımı yeniden aç'}</Button>}
 </Surface>}</div>;
}
