'use client';
import {useEffect,useRef,useState} from 'react';
import type {Project} from '../lib/projects';
import {api} from '../lib/api';
import {Alert,Button,Checkbox,Field,Select,Surface} from './ui';

type Content={kind:string;text?:string;rows?:string[][];images?:{data_url:string;width:number;height:number}[];truncated:boolean;total_pages?:number};
type FileInfo={id:string;filename:string;kind:string;size:number;source_commit:string;created_at:string};
type Preview=FileInfo & {content:Content;expires_at?:string};
type Directory={path:string;source_commit:string;entries:{name:string;path:string;type:'file'|'directory';size:number}[]};
const size=(bytes:number)=>bytes<1048576?`${Math.ceil(bytes/1024)} KB`:`${(bytes/1048576).toFixed(1)} MB`;
function FileContent({file}:{file:Preview}) {
 const content=file.content;
 return <div className="showcase-preview"><p className="field-help">{file.filename} · {size(file.size)} · Sürüm {file.source_commit.slice(0,10)}</p>
 {content.kind==='csv'?<div className="file-table-scroll" tabIndex={0} role="region" aria-label={`${file.filename} CSV önizlemesi`}><table className="file-table"><caption>{file.filename}</caption><tbody>{content.rows?.map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j}>{cell}</td>)}</tr>)}</tbody></table></div>:content.kind==='image'||content.kind==='pdf'?<div className="file-pages">{content.images?.map((page,i)=>/^data:image\/jpeg;base64,[A-Za-z0-9+/]+=*$/.test(page.data_url)?<figure key={i}><img src={page.data_url} width={page.width} height={page.height} alt={content.kind==='pdf'?`${file.filename}, sayfa ${i+1}`:file.filename}/>{content.kind==='pdf'&&<figcaption>Sayfa {i+1} / {content.total_pages}</figcaption>}</figure>:<Alert key={i} tone="error">Önizleme görüntüsü yüklenemedi.</Alert>)}</div>:<><p className="field-help">{content.kind==='markdown'?'Markdown güvenli düz metin olarak gösterilir.':'Metin önizlemesi.'}</p><pre className="file-text" tabIndex={0}>{content.text}</pre></>}
 {content.truncated&&<Alert>Önizleme kısaltıldı. {content.kind==='pdf'?'En fazla ilk 6 sayfa gösterilir.':content.kind==='image'?'Animasyonun yalnız ilk karesi gösterilir.':'CSV önizlemesi ilk 200 satır, 30 sütun ve hücre başına 2.000 karakterle sınırlıdır.'}</Alert>}
 </div>;
}
export function ShowcasePanel({project}:{project:Project}) {
 const base=`showcase/projects/${project.id}`;
 const [files,setFiles]=useState<FileInfo[]|null>(null),[selected,setSelected]=useState<Preview|null>(null),[prepared,setPrepared]=useState<Preview|null>(null);
 const [directory,setDirectory]=useState<Directory|null>(null),[editing,setEditing]=useState(false),[replacement,setReplacement]=useState('');
 const [confirmed,setConfirmed]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[reload,setReload]=useState(0);
 const lock=useRef(false),alive=useRef(true);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 useEffect(()=>{let current=true;setFiles(null);setSelected(null);api<{files:FileInfo[]}>(`${base}/files`).then(data=>{if(current)setFiles(data.files);}).catch(caught=>{if(current)setError(caught.message);});return()=>{current=false;};},[base,reload]);
 async function perform(work:()=>Promise<void>){if(lock.current)return;lock.current=true;setBusy(true);setError('');setNotice('');try{await work();}catch(caught){if(alive.current)setError((caught as Error).message);}finally{lock.current=false;if(alive.current)setBusy(false);}}
 async function browse(path:string){const data=await api<Directory>(`${base}/browse`,undefined,'GET',new URLSearchParams({path}));if(alive.current)setDirectory(data);}
 function refresh(){setSelected(null);setReload(value=>value+1);}
 return <Surface className="project-detail file-showcase"><div className="page-toolbar"><div><h2>Dosya vitrini</h2><p className="field-help">Proje sahibinin yayımladığı dosya sürümleri. Repodaki değişiklikler otomatik aktarılmaz.</p></div>{project.is_owner&&project.is_active&&!editing&&<Button variant="secondary" disabled={busy} onClick={()=>void perform(async()=>{await browse('');if(alive.current)setEditing(true);})}>Dosyaları yönet</Button>}</div>
 {error&&<Alert tone="error" role="alert">{error} {!files&&<Button variant="secondary" onClick={()=>{setError('');refresh();}}>Yeniden yükle</Button>}</Alert>}{notice&&<Alert tone="success" role="status">{notice}</Alert>}
 {files===null&&!error?<p role="status">Dosyalar yükleniyor…</p>:files?.length===0?<p>Henüz paylaşılan dosya yok.</p>:<ul className="file-list">{files?.map(file=><li key={file.id}><Button variant="quiet" disabled={busy} aria-pressed={selected?.id===file.id} onClick={()=>void perform(async()=>{setSelected(null);const data=await api<{file:Preview}>(`${base}/files/${file.id}/preview`);if(alive.current)setSelected(data.file);})}>{file.filename} <span className="field-help">{size(file.size)}</span></Button>{project.is_owner&&<Button variant="quiet" disabled={busy} onClick={()=>{if(window.confirm(`${file.filename} vitrinden kaldırılsın mı? GitHub’daki dosya değişmez.`))void perform(async()=>{await api(`${base}/files/${file.id}`,{},'DELETE');if(alive.current){refresh();setNotice('Dosya vitrinden kaldırıldı.');}});}}>Kaldır</Button>}</li>)}</ul>}
 {selected&&<FileContent file={selected}/>}
 {editing&&project.is_owner&&<div className="file-editor"><h3>Repodan dosya seç</h3><p className="field-help">En fazla 3 dosya, toplam 20 MB. UTF-8 metin / Markdown / CSV: 1 MB; PNG / JPEG / WebP / PDF: 10 MB. Office, arşiv, SVG ve diğer ikili dosyalar desteklenmez. PDF’de bazı yazı tipleri farklı görünebilir; yayımlamadan önce önizlemeyi inceleyin.</p>
 {!prepared&&<><Field id="showcase-replacement" label="Yayın işlemi"><Select id="showcase-replacement" value={replacement} disabled={busy} onChange={event=>setReplacement(event.target.value)}><option value="">Yeni dosya ekle</option>{files?.map(file=><option key={file.id} value={file.id}>{file.filename} yerine yayımla</option>)}</Select></Field>
 <div className="file-browser"><div className="action-row"><strong className="file-path">{directory?.path||'Repo kökü'}</strong>{directory?.path&&<Button variant="quiet" disabled={busy} onClick={()=>void perform(()=>browse(directory.path.split('/').slice(0,-1).join('/')))}>Üst klasör</Button>}</div>
 <ul className="file-list">{directory?.entries.map(entry=><li key={entry.path}><Button variant="quiet" disabled={busy||(!replacement&&(files?.length??0)>=3)} onClick={()=>void perform(async()=>{if(entry.type==='directory'){await browse(entry.path);return;}const data=await api<{preview:Preview}>(`${base}/prepare`,{path:entry.path});if(alive.current){setPrepared(data.preview);setConfirmed(false);}})}>{entry.type==='directory'?'Klasör: ':''}{entry.name}{entry.type==='file'&&<span className="field-help">{size(entry.size)}</span>}</Button></li>)}</ul>{directory?.entries.length===0&&<p>Bu klasörde seçilebilir dosya yok.</p>}</div>
 {!replacement&&(files?.length??0)>=3&&<Alert>Üç dosya yayımlanmış. Değiştirilecek dosyayı seçin veya birini kaldırın.</Alert>}</>}
 {prepared&&<><h3>Yayımlanacak önizleme</h3><FileContent file={prepared}/><p className="field-help">Bu önizleme 30 dakika geçerlidir. Yayımlanan sürüm, siz değiştirene veya kaldırana kadar saklanır.</p><Checkbox checked={confirmed} disabled={busy} onChange={event=>setConfirmed(event.target.checked)}>Önizlemeyi kontrol ettim; gizli bilgi içermiyor ve ilanı görebilen herkesle paylaşılmasını onaylıyorum.</Checkbox><div className="action-row"><Button loading={busy} disabled={!confirmed} onClick={()=>void perform(async()=>{await api(`${base}/publish`,{preview_id:prepared.id,...(replacement?{replace_id:replacement}:{}),confirmed:true});if(alive.current){setPrepared(null);setConfirmed(false);setEditing(false);setDirectory(null);setReplacement('');refresh();setNotice('Dosya vitrinde yayımlandı.');}})}>{replacement?'Dosyayı değiştir':'Yayımla'}</Button><Button variant="secondary" disabled={busy} onClick={()=>void perform(async()=>{await api(`${base}/prepare/${prepared.id}`,{},'DELETE');if(alive.current){setPrepared(null);setConfirmed(false);}})}>Seçimi iptal et</Button></div></>}
 {!prepared&&<Button variant="quiet" disabled={busy} onClick={()=>{setEditing(false);setDirectory(null);}}>Yönetimi kapat</Button>}
 </div>}{busy&&<p role="status">İşlem sürüyor…</p>}
 </Surface>;
}
