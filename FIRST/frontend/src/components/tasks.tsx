'use client';

import Link from 'next/link';
import {useEffect, useRef, useState, type FormEvent, type ReactNode} from 'react';
import {api} from '../lib/api';
import {githubResourceUrl, type Project} from '../lib/projects';
import {SessionPending, useSession} from './session-provider';
import {ActionLink, Alert, Button, Checkbox, Field, Input, PageHeading, Select, Surface} from './ui';

type Task = {request_id?:string|null;id:string;project_id:string;project_title:string;issue_number:number|null;title:string;body:string;state:string;issue_url:string;synced_at:string|null;operation_state:string;operation_error:string};
type TaskPage = {tasks:Task[];next_cursor:string|null;has_more:boolean};
type Draft = {request_id:string;title:string;body:string};
const message = (error:unknown) => error instanceof Error ? error.message : 'İşlem tamamlanamadı.';

function TaskCard({task, children}:{task:Task;children?:ReactNode}) {
  const url = githubResourceUrl(task.issue_url);
  const ready = task.operation_state === 'ready';
  return <Surface className="task-card account-section">
    <div className="project-card-heading"><h3>{task.issue_number ? `#${task.issue_number} · ` : ''}{task.title}</h3><span className={`connection-status${ready && task.state === 'open' ? ' connection-status--connected' : ''}`}>{!ready ? 'Sonuç doğrulanmalı' : task.state === 'closed' ? 'Kapalı' : 'Açık'}</span></div>
    <Link href={`/projeler/${task.project_id}`}>{task.project_title}</Link>
    {task.body && <details className="project-editor-details"><summary>Görev açıklaması</summary><p className="project-text">{task.body}</p></details>}
    {ready && <p className="field-help">Son alınan durum{task.synced_at ? ` · ${new Date(task.synced_at).toLocaleString('tr-TR')}` : ''}. GitHub değişiklikleri otomatik yansımaz.</p>}
    {!ready && <Alert>GitHub işleminin sonucu henüz doğrulanamadı. Tekrar kontrol etmek aynı oluşturma işlemini uzlaştırır.</Alert>}
    <div className="action-row">{url && <ActionLink variant="quiet" href={url} target="_blank" rel="noreferrer">GitHub Issue ↗</ActionLink>}{children}</div>
  </Surface>;
}

export function TasksPage() {
  const {status, user} = useSession();
  if(status !== 'ready') return <SessionPending/>;
  return <TaskDiscovery key={user?.id ?? 'guest'}/>;
}
function TaskDiscovery() {
  const [q,setQ] = useState('');
  const [state,setState] = useState('open');
  const [projectId,setProjectId] = useState('');
  const [projects,setProjects] = useState<Record<string,string>>({});
  const [query,setQuery] = useState({q:'',state:'open',project_id:'',cursor:''});
  const [page,setPage] = useState<TaskPage|null>(null);
  const [error,setError] = useState('');
  const [revision,setRevision] = useState(0);
  useEffect(() => {
    let active = true; setPage(null); setError('');
    const params = new URLSearchParams();
    for(const [key,value] of Object.entries(query)) if(value) params.set(key,value);
    api<TaskPage>('tasks',undefined,'GET',params).then(result=>{if(active){setPage(result);setProjects(previous=>({...previous,...Object.fromEntries(result.tasks.map(task=>[task.project_id,task.project_title]))}));}}).catch(error=>{if(active)setError(message(error));});
    return ()=>{active=false;};
  },[query,revision]);
  function search(event:FormEvent) {event.preventDefault(); setQuery({q:q.trim(),state,project_id:projectId.trim(),cursor:''});}
  return <>
    <PageHeading eyebrow="FIRST / GÖREVLER" title="Katkı verecek bir görev bul" description="Public projelerin GitHub Issue görevlerini keşfet. Görev atama veya rezervasyon yapılmaz."/>
    <Surface className="project-panel"><form onSubmit={search}><div className="listing-filters">
      <Field id="task-query" label="Görev veya proje ara"><Input id="task-query" value={q} maxLength={100} onChange={event=>setQ(event.target.value)}/></Field>
      <Field id="task-state" label="Durum"><Select id="task-state" value={state} onChange={event=>setState(event.target.value)}><option value="open">Açık</option><option value="closed">Kapalı</option><option value="all">Tümü</option></Select></Field>
      <Field id="task-project" label="Proje" help="Sonuçlarda görünen bir projeye odaklanın veya proje adıyla arayın."><Select id="task-project" value={projectId} onChange={event=>setProjectId(event.target.value)}><option value="">Tüm projeler</option>{Object.entries(projects).map(([id,name])=><option key={id} value={id}>{name}</option>)}</Select></Field>
    </div><Button type="submit">Görevleri bul</Button></form></Surface>
    {error && <Alert tone="error" role="alert"><p>{error}</p><Button variant="secondary" onClick={()=>setRevision(value=>value+1)}>Yeniden dene</Button></Alert>}
    {!page && !error && <Alert role="status">Görevler yükleniyor…</Alert>}
    {page && <><div className="task-list">{page.tasks.map(task=><TaskCard key={task.id} task={task}/>)}</div>
      {!page.tasks.length && <Alert>Bu sonuç grubunda eşleşen görev yok.{page.has_more ? ' Daha fazla sonuç kontrol edebilirsiniz.' : ''}</Alert>}
      <div className="pagination">{query.cursor && <Button variant="quiet" onClick={()=>setQuery(value=>({...value,cursor:''}))}>İlk sonuçlara dön</Button>}{page.has_more && page.next_cursor && <Button variant="secondary" onClick={()=>setQuery(value=>({...value,cursor:page.next_cursor!}))}>Sonraki sonuçları kontrol et</Button>}</div>
    </>}
  </>;
}

export function ProjectTasks({project}:{project:Project}) {
  const {status,user} = useSession();
  if(project.is_private || status !== 'ready') return null;
  return <ProjectTaskContent key={`${project.id}:${user?.id ?? 'guest'}:${project.is_owner}`} project={project} identity={user?.id ?? null}/>;
}
function ProjectTaskContent({project,identity}:{project:Project;identity:number|null}) {
  const own = project.is_owner && identity !== null;
  const storageKey = `first.task-create:${identity}:${project.id}`;
  const [tasks,setTasks] = useState<Task[]|null>(null);
  const [error,setError] = useState('');
  const [notice,setNotice] = useState('');
  const [revision,setRevision] = useState(0);
  const [busy,setBusy] = useState('');
  const [mode,setMode] = useState('attach');
  const [number,setNumber] = useState('');
  const [title,setTitle] = useState('');
  const [body,setBody] = useState('');
  const [draft,setDraft] = useState<Draft|null>(null);
  const [checkedPrevious,setCheckedPrevious] = useState(false);
  const lock = useRef(false);
  const mounted = useRef(true);
  useEffect(()=>{mounted.current=true; return ()=>{mounted.current=false;};},[]);
  useEffect(()=>{
    if(!own) return;
    try {
      const saved = sessionStorage.getItem(storageKey);
      if(saved) {
        const value = JSON.parse(saved) as Draft;
        if(typeof value.request_id === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value.request_id) && typeof value.title === 'string' && value.title.trim().length > 0 && value.title.length <= 200 && typeof value.body === 'string' && value.body.length <= 10000) {setDraft(value);setTitle(value.title);setBody(value.body);setMode('create');}
        else {sessionStorage.removeItem(storageKey);setError('Geçersiz oluşturma taslağı kaldırıldı. Başlık ve açıklamayı yeniden girin.');}
      }
    } catch {setError('Önceki oluşturma işlemi okunamadı. Yeni Issue oluşturmadan önce aşağıdaki görevleri kontrol edin.');}
  },[own,storageKey]);
  useEffect(()=>{
    let active=true; setTasks(null);
    api<{tasks:Task[]}>(`tasks/projects/${project.id}`).then(result=>{if(active)setTasks(result.tasks);}).catch(error=>{if(active)setError(message(error));});
    return ()=>{active=false;};
  },[project.id,revision]);
  function clearDraft() {sessionStorage.removeItem(storageKey);setDraft(null);setTitle('');setBody('');setCheckedPrevious(false);}
  async function submit(event:FormEvent) {
    event.preventDefault(); if(lock.current) return;
    if(mode==='create' && !title.trim()) {setError('Görev başlığı yalnız boşluklardan oluşamaz.');return;}
    lock.current=true;setBusy('submit');setError('');setNotice('');
    try {
      let payload:Draft|{issue_number:number};
      if(mode==='attach') payload={issue_number:Number(number)};
      else {
        const pending=draft || {request_id:crypto.randomUUID(),title:title.trim(),body};
        // Save before POST so reload/network failure keeps the exact id and payload.
        sessionStorage.setItem(storageKey,JSON.stringify(pending));setDraft(pending);payload=pending;
      }
      const result=await api<{task:Task}>(`tasks/projects/${project.id}`,payload);
      if(!mounted.current)return;
      if(mode==='create' && result.task.operation_state==='ready')clearDraft();
      setNumber('');setNotice(result.task.operation_state==='ready' ? 'Görev FIRST’e bağlandı.' : 'İşlem kaydedildi; GitHub sonucu doğrulanmalı.');
    } catch(error) {if(mounted.current)setError(message(error));}
    finally {lock.current=false;if(mounted.current){setBusy('');setRevision(value=>value+1);}}
  }
  async function update(task:Task,action:'refresh'|'retry'|'remove') {
    if(lock.current)return;
    lock.current=true;setBusy(task.id);setError('');setNotice('');
    try {
      if(action==='remove') {await api(`tasks/${task.id}`,{},'DELETE');if(mounted.current)setNotice('FIRST bağlantısı kaldırıldı. GitHub Issue değiştirilmedi.');}
      else {
        const result=await api<{task:Task}>(`tasks/${task.id}/${action}`,{});
        if(!mounted.current)return;
        if(action==='retry' && result.task.operation_state==='ready' && draft && result.task.request_id===draft.request_id)clearDraft();
        setNotice(result.task.operation_state==='ready' ? 'Görev durumu güncellendi.' : 'Sonuç henüz doğrulanamadı.');
      }
    } catch(error) {if(mounted.current)setError(message(error));}
    finally {lock.current=false;if(mounted.current){setBusy('');setRevision(value=>value+1);}}
  }
  return <section className="participation-section" aria-labelledby="project-tasks-title">
    <h2 id="project-tasks-title">GitHub görevleri</h2><p className="field-help">GitHub Issue kayıtlarının son alınan hâli. Atama ve rezervasyon yoktur.</p>
    {error && <Alert tone="error" role="alert">{error}</Alert>}{notice && <Alert tone="success" role="status">{notice}</Alert>}
    {own && <details className="project-editor-details"><summary>Görev bağla veya oluştur</summary><form onSubmit={submit}><fieldset disabled={!!busy}>
      <Field id="task-mode" label="İşlem"><Select id="task-mode" value={mode} onChange={event=>setMode(event.target.value)}><option value="attach">Mevcut Issue bağla</option><option value="create">GitHub’da yeni Issue oluştur</option></Select></Field>
      {mode==='attach' ? <Field id="task-number" label="Issue numarası"><Input id="task-number" type="number" min={1} step={1} required value={number} onChange={event=>setNumber(event.target.value)}/></Field> : <>
        {draft && <Alert><p>Önceki oluşturma isteği korunuyor. Aynı isteği kontrol etmek yeni bir işlem kimliği üretmez. Başlık ve açıklama bu işlem için değiştirilemez.</p>
          <p>Başka bir görev hazırlamak önceki GitHub işlemini iptal etmez. Varsa aşağıdaki bekleyen kayıt korunur; sonucunu oradan doğrulayabilirsiniz.</p>
          <Checkbox checked={checkedPrevious} onChange={event=>setCheckedPrevious(event.target.checked)}>GitHub’daki Issue kayıtlarını kontrol ettim; önceki isteği tekrarlamak yerine farklı bir görev hazırlayacağım.</Checkbox>
          <Button variant="quiet" disabled={!checkedPrevious} onClick={()=>{try {clearDraft();setNotice('Form yeni görev için temizlendi. Önceki sunucu kaydı ve GitHub Issue değiştirilmedi.');} catch(error) {setError(message(error));}}}>Farklı bir görev hazırla</Button>
        </Alert>}
        <Field id="task-title" label="Başlık"><Input id="task-title" required maxLength={200} value={title} readOnly={!!draft} onChange={event=>setTitle(event.target.value)}/></Field>
        <Field id="task-body" label="Açıklama"><textarea id="task-body" className="input" rows={4} maxLength={10000} value={body} readOnly={!!draft} onChange={event=>setBody(event.target.value)}/></Field>
        <p className="field-help">Bu işlem GitHub reponuzda public bir Issue oluşturur.</p>
      </>}
      <Button type="submit" loading={busy==='submit'}>{mode==='attach' ? 'Issue bağla' : draft ? 'Aynı oluşturma isteğini kontrol et' : 'GitHub’da Issue oluştur'}</Button>
    </fieldset></form></details>}
    {!tasks && !error && <Alert role="status">Görevler yükleniyor…</Alert>}
    {tasks?.length===0 && <p>Henüz görev bağlanmamış.</p>}
    <div className="task-list">{tasks?.map(task=><TaskCard key={task.id} task={task}>{own && <>
      <Button variant="secondary" disabled={!!busy} loading={busy===task.id} onClick={()=>void update(task,task.operation_state==='ready' ? 'refresh':'retry')}>{task.operation_state==='ready' ? 'Durumu yenile' : 'Oluşturma sonucunu doğrula'}</Button>
      {task.operation_state==='ready' && <Button variant="quiet" disabled={!!busy} onClick={()=>void update(task,'remove')}>FIRST bağlantısını kaldır</Button>}
    </>}</TaskCard>)}</div>
    <Button variant="quiet" disabled={!!busy} onClick={()=>{setError('');setRevision(value=>value+1);}}>Listeyi yeniden yükle</Button>
  </section>;
}
