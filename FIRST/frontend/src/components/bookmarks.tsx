'use client';
import {useEffect,useRef,useState} from 'react';
import {api} from '../lib/api';
import type {PageInfo} from '../lib/community';
import type {ProjectSummary} from '../lib/projects';
import {Pagination} from './community-controls';
import {ProjectCard} from './project-card';
import {RequireSession} from './session-provider';
import {ActionLink,Alert,Button,PageHeading,Surface} from './ui';
type Bookmarks=PageInfo&{bookmarks:{project_id:string;project:ProjectSummary|null;available:boolean}[]};
export function SavedProjects(){return <RequireSession><SavedContent/></RequireSession>;}
function SavedContent(){
 const [page,setPage]=useState(1);const [data,setData]=useState<Bookmarks|null>(null);const [error,setError]=useState('');const [retry,setRetry]=useState(0);const [busy,setBusy]=useState('');const lock=useRef(false);
 useEffect(()=>{let active=true;setData(null);setError('');api<Bookmarks>('bookmarks',undefined,'GET',new URLSearchParams({page:String(page)})).then(d=>{if(active)setData(d);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[page,retry]);
 return <div className="community-page"><PageHeading title="Kaydedilen projeler" description="Bu listeyi yalnız siz görebilirsiniz."/>{error&&<Alert tone="error" role="alert"><p>{error}</p><Button variant="secondary" onClick={()=>setRetry(v=>v+1)}>Yeniden dene</Button></Alert>}{!data&&!error&&<Alert role="status">Kaydedilenler yükleniyor…</Alert>}{data&&<><p>{data.count} kayıt</p><div className="repository-grid">{data.bookmarks.map(item=><div className="saved-project" key={item.project_id}>{item.available&&item.project?<ProjectCard project={item.project}/>:<Surface className="project-panel"><h2>Proje şu anda görüntülenemiyor</h2><p>Arşivlenmiş veya erişiminiz değişmiş olabilir.</p></Surface>}<Button variant="quiet" disabled={!!busy} loading={busy===item.project_id} onClick={async()=>{if(lock.current)return;lock.current=true;setBusy(item.project_id);setError('');try{await api(`projects/${item.project_id}/bookmark`,{},'DELETE');if(data.bookmarks.length===1&&page>1)setPage(page-1);else setRetry(v=>v+1);}catch(e){setError((e as Error).message);}finally{lock.current=false;setBusy('');}}}>Kaydedilenlerden çıkar</Button></div>)}</div>{!data.bookmarks.length&&<Surface className="empty-state"><p>Henüz kaydedilmiş proje yok.</p><ActionLink href="/">Projeleri keşfet</ActionLink></Surface>}<Pagination data={data} page={page} onChange={setPage}/></>}</div>;
}
