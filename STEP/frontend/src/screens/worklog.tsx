"use client";
import { useEffect, useState, type FormEvent } from "react";
import { blob, date, money } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import { Action, Field, Notice, Panel, State, Status, TaskForm, value } from "@/components/ui";
import { useSession } from "@/components/session";
import type { Block, Contract, Screenshot, Worklog } from "@/lib/types";
export function ScreenshotView({ screenshot, own, permitted, refresh }: { screenshot:Screenshot; own:boolean; permitted:boolean; refresh:()=>void }) {
  const [image,setImage]=useState<string|null>(null);
  const [loading,setLoading]=useState(false);
  const [loadError,setLoadError]=useState<string|null>(null);
  const [seen,setSeen]=useState(false);
  const [confirmed,setConfirmed]=useState(false);
  const mutation=useMutation();
  useEffect(()=>()=>{if(image)URL.revokeObjectURL(image);},[image]);
  async function load() { setLoading(true);setLoadError(null);try{const result=await blob(`screenshots/${screenshot.id}/image/`);setImage(URL.createObjectURL(result));setSeen(true);}catch(error){setLoadError(error instanceof Error?error.message:"Görüntü alınamadı.");}finally{setLoading(false);} }
  async function act(action:"publish"|"review-ready"|"privacy",body:unknown={}) { try{await mutation.submit(`screenshots/${screenshot.id}/${action}/`,{method:"POST",body},action==="privacy"?"Talep moderasyona gönderildi. Görüntü işverene kapalı tutulur.":action==="publish"?"Görüntü yayımlandı.":"Önizleme tamamlandı. Yapılandırılmış yayın bekleme süresi başlatıldı.");refresh();}catch{} }
  return <div className="details">
<div className="meta">
<Status value={screenshot.state}/>
<span>{date(screenshot.captured_at)}</span>
</div>{permitted?<button type="button" className="button button-small button-secondary" disabled={loading||mutation.busy} onClick={()=>void load()}>{loading?"Alınıyor…":image?"Görüntüyü yenile":"Görüntüyü güvenli aç"}</button>:<p className="muted">Bu görüntü için erişim yetkiniz yok veya görüntü henüz yayımlanmadı.</p>}{loadError?<Notice tone="error">{loadError}</Notice>:null}{image?<p>
<img className="work-image" src={image} alt="İlgili çalışma bölümünün ekran görüntüsü"/>
</p>:null}{own&&screenshot.state==="preview"?<>
<p>Görüntü şu anda yalnız size açıktır. Kişisel bilgi içeriyorsa yayımlamadan önce inceleme isteyin.</p>
<form onSubmit={(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();void act("privacy",{reason:value(new FormData(event.currentTarget),"reason")});}}>
<fieldset disabled={mutation.busy}>
<Field field={{name:"reason",label:"Kişisel bilgi talebi gerekçesi",type:"textarea",required:true}}/>
<button className="button button-secondary" type="submit">Moderasyon talebi aç</button>
</fieldset>
</form>
<label className="field field-checkbox">
<input type="checkbox" checked={confirmed} onChange={event=>setConfirmed(event.target.checked)} disabled={!seen||mutation.busy}/>Görüntüyü inceledim; kişisel bilgi olmadığını teyit ediyorum.</label>
<div className="actions">
<button className="button button-small" disabled={!seen||!confirmed||mutation.busy} onClick={()=>void act("publish")}>Görüntüyü yayımla</button>
<button className="button button-small button-secondary" disabled={!seen||!confirmed||mutation.busy} onClick={()=>void act("review-ready")}>Önizlemeyi bitir</button>
</div>
<p className="muted">Önizlemeyi bitirme, yalnız yayın bekleme süresi ayarlanmışsa otomatik yayın sayacını başlatır.</p>
</>:null}{screenshot.state==="held"?<Notice>Moderasyon bitene kadar bütün işveren erişimleri kapalıdır. Talep çalışma süresini veya ücreti otomatik azaltmaz.</Notice>:null}{mutation.error?<Notice tone="error">{mutation.error}</Notice>:null}{mutation.success?<Notice tone="success">{mutation.success}</Notice>:null}</div>;
}
function WorkBlock({ block, employer, userId, refresh }: { block:Block; employer:boolean; userId:string; refresh:()=>void }) { const own=block.owner===userId; return <article className="card">
<h3>{block.owner_name|| (own?"Çalışmam":"Çalışan kaydı")}</h3>
<p>{date(block.starts_at)} — {date(block.ends_at)}</p>
<p>{(block.seconds/60).toFixed(1)} dakika · {block.active_app}</p>{block.memo?<p>{block.memo}</p>:null}<p className="muted">Klavye etkinliği: {block.key_count} · Fare etkinliği: {block.mouse_count}. Tuş içeriği kaydedilmez.</p>{block.screenshot?<ScreenshotView screenshot={block.screenshot} own={own} permitted={own||(employer&&block.screenshot.state==="released")} refresh={refresh}/>:null}</article>; }
export function WorklogSection({ contract, data, loading, error, reload }: { contract:Contract; data:Worklog|null; loading:boolean; error:string|null; reload:()=>void }) { const {user}=useSession();
  const employer=contract.employer===user?.id; return <Panel title="Çalışma günlüğü">
<State loading={loading} error={error} retry={reload}>{data?<>
<p className="muted">{data.summary.basis==="fixed_target_amount"?"Aşama tutarlarına dayalı sabit iş hesabı":data.summary.basis==="hourly_worked_amount"?"Kayıtlı ve onaylı süreye dayalı saatlik iş hesabı":"Hesap esası alınamadı"}. Bu toplam banka aktarımı veya kesinleşmiş kazanç kanıtı değildir.</p>
<div className="meta">
<span>Toplam {(data.summary.seconds/3600).toFixed(2)} saat</span>
<span>Brüt {money(data.summary.gross)}</span>
<span>Net {money(data.summary.net)}</span>
</div>
<div className="card-list">{data.blocks.map(block=>
<WorkBlock key={block.id} block={block} employer={employer} userId={user?.id||""} refresh={reload}/>)}</div>{!data.blocks.length?<p className="empty">Takip kaydı yok. Çalışma kaydı masaüstü istemcisinden gelir.</p>:null}<h3>Manuel süreler</h3>{data.manual_time.map(item=>
<article key={item.id} className="card">
<div className="meta">
<span>{item.owner_name||"Çalışan"}</span>
<Status value={item.status}/>
</div>
<p>{date(item.starts_at)} — {date(item.ends_at)}</p>
<p>{item.memo}</p>{employer&&item.status==="pending"?<div className="actions">
<Action path={`manual-time/${item.id}/review/`} body={{decision:"approve"}} label="Süreyi ücretlendirmeyi onayla" onSuccess={reload}/>
<Action path={`manual-time/${item.id}/review/`} body={{decision:"reject"}} label="Manuel süreyi reddet" onSuccess={reload}/>
</div>:null}</article>)}</>:null}</State>
</Panel>; }
