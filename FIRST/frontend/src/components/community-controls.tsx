'use client';
import {useEffect,useRef,useState} from 'react';
import {api} from '../lib/api';
import type {TaxonomyOption} from '../lib/projects';
import type {CommunityConfig,PageInfo} from '../lib/community';
import {useSession} from './session-provider';
import {ActionLink,Alert,Button,Checkbox,Field,Select} from './ui';
export function MultiChoice({label,options,value,onChange,max=12}:{label:string;options:TaxonomyOption[];value:string[];onChange:(value:string[])=>void;max?:number}){
 return <fieldset className="community-choices"><legend>{label} <span className="field-help">({value.length}/{max})</span></legend><details><summary>Seçenekleri düzenle</summary><div className="community-choice-options">{options.map(item=><Checkbox key={item.value} checked={value.includes(item.value)} disabled={!value.includes(item.value)&&value.length>=max} onChange={event=>onChange(event.target.checked?[...value,item.value]:value.filter(v=>v!==item.value))}>{item.label}</Checkbox>)}</div></details><p className="field-help">{value.length?options.filter(item=>value.includes(item.value)).map(item=>item.label).join(" · "):"Henüz seçim yapılmadı."}</p></fieldset>;
}
export function Pagination({data,page,onChange}:{data:PageInfo;page:number;onChange:(page:number)=>void}){return data.next_page||data.previous_page?<nav className="pagination" aria-label="Sonuç sayfaları"><Button variant="secondary" disabled={!data.previous_page} onClick={()=>data.previous_page&&onChange(data.previous_page)}>← Önceki</Button><span aria-live="polite">Sayfa {page}</span><Button variant="secondary" disabled={!data.next_page} onClick={()=>data.next_page&&onChange(data.next_page)}>Sonraki →</Button></nav>:null;}
export function BookmarkButton({id}:{id:string}){
 const {user,status}=useSession();
 return status==='ready'&&user?<BookmarkControl key={`${user.id}:${id}`} id={id}/>:status==='ready'?<ActionLink variant="quiet" href="/giris">Kaydetmek için giriş yap</ActionLink>:null;
}
function BookmarkControl({id}:{id:string}){
 const [saved,setSaved]=useState<boolean|null>(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [retry,setRetry]=useState(0);const lock=useRef(false);
 useEffect(()=>{let active=true;api<{saved:boolean}>(`projects/${id}/bookmark`).then(data=>{if(active)setSaved(data.saved);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[id,retry]);
 return <div>{error&&<Alert role="alert" tone="error">{error}</Alert>}{saved===null?<Button variant="secondary" disabled={!error} onClick={()=>{setError('');setRetry(v=>v+1);}}>{error?'Kaydetme durumunu yeniden yükle':'Kaydetme durumu yükleniyor…'}</Button>:<Button variant="secondary" aria-pressed={saved} loading={busy} onClick={async()=>{if(lock.current)return;lock.current=true;setBusy(true);setError('');try{setSaved((await api<{saved:boolean}>(`projects/${id}/bookmark`,{},saved?'DELETE':'PUT')).saved);}catch(e){setError((e as Error).message);}finally{lock.current=false;setBusy(false);}}}>{saved?'Kaydedilenlerden çıkar':'Projeyi kaydet'}</Button>}</div>;
}
export function ReportForm({type,id,own=false}:{type:'project'|'profile';id:string;own?:boolean}){
 const {user,status}=useSession();
 if(own||status!=='ready')return null;
 if(!user)return <ActionLink href="/giris" variant="quiet">Şikâyet için giriş yap</ActionLink>;
 if(!user.email_verified)return <p className="field-help">Şikâyet göndermek için <a href="/hesap">e-postanızı doğrulayın</a>.</p>;
 return <ReportContent key={`${user.id}:${type}:${id}`} type={type} id={id}/>;
}
function ReportContent({type,id}:{type:'project'|'profile';id:string}){
 const [open,setOpen]=useState(false);const [config,setConfig]=useState<CommunityConfig|null>(null);const [reason,setReason]=useState('');const [description,setDescription]=useState('');const [error,setError]=useState('');const [message,setMessage]=useState('');const [busy,setBusy]=useState(false);const lock=useRef(false);
 async function load(){setError('');try{setConfig(await api<CommunityConfig>('community/config'));}catch(e){setError((e as Error).message);}}
 return <div className="community-report"><Button variant="quiet" aria-expanded={open} onClick={()=>{setOpen(!open);if(!open&&!config)void load();}}>Şikâyet bildir</Button>{open&&<form onSubmit={async event=>{event.preventDefault();if(lock.current)return;lock.current=true;setBusy(true);setError('');setMessage('');try{const data=await api<{created:boolean}>('reports',{target_type:type,target_id:id,reason,description:description.trim()});setMessage(data.created?'Şikâyetiniz kaydedildi.':'Bu içerik için şikâyetiniz zaten kaydedilmiş.');setDescription('');}catch(e){setError((e as Error).message);}finally{lock.current=false;setBusy(false);}}}>{error&&<Alert role="alert" tone="error">{error}</Alert>}{message&&<Alert role="status" tone="success">{message}</Alert>}{!config?<Button variant="secondary" onClick={()=>void load()}>Nedenleri yükle</Button>:<fieldset disabled={busy}><Field id={`report-reason-${id}`} label="Şikâyet nedeni"><Select id={`report-reason-${id}`} value={reason} onChange={e=>setReason(e.target.value)} required><option value="">Bir neden seçin</option>{config.report_reasons.map(item=><option key={item.value} value={item.value}>{item.label}</option>)}</Select></Field><Field id={`report-description-${id}`} label="Açıklama"><textarea className="input" id={`report-description-${id}`} rows={3} minLength={10} maxLength={2000} required value={description} onChange={e=>setDescription(e.target.value)}/></Field><Button type="submit" loading={busy} disabled={description.trim().length<10}>Şikâyeti gönder</Button></fieldset>}</form>}</div>;
}
