"use client";
import { Action, Notice, Status } from "@/components/ui";
import { money } from "@/lib/api";
import type { Contract, ContractChange, ContractTerms, ContractMember, MilestoneTerms, PublicProfile } from "@/lib/types";

const textReady = (value: unknown): value is string => typeof value === "string" && value.trim().length > 0;
const readableText = (value:unknown) => typeof value === "string" ? value : "Şart alınamadı";
const numberReady = (value: unknown) => typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value)) && Number(value) >= 0;
function TermRow({label,before,after}:{label:string;before:string;after:string}) {return <tr><th scope="row">{label}</th><td className="long-text">{before}</td><td className="long-text">{after}{before===after?<small className="muted"> · Değişmiyor</small>:null}</td></tr>;}

export function ContractChangeCard({contract,change,people,inventoryReady,userId,canAccept,refresh}:{contract:Contract;change:ContractChange;people:PublicProfile[];inventoryReady:boolean;userId:string;canAccept:boolean;refresh:()=>void}) {
  const input=change.terms;
  const terms:ContractTerms={scope:contract.scope,revision_terms:contract.revision_terms,expected_duration:contract.expected_duration,tracker_required:contract.tracker_required,rate:contract.rate,weekly_limit:contract.weekly_limit,members:contract.members,milestones:contract.milestones,...input};
  if (!contract.team) terms.members = contract.members.map(member => ({...member,hourly_rate:terms.rate??member.hourly_rate}));
  const memberRows:unknown=terms.members; const stageRows:unknown=terms.milestones;
  const members=Array.isArray(memberRows)?memberRows.filter((item):item is ContractMember=>Boolean(item&&typeof item==="object"&&typeof item.user==="string"&&typeof item.hourly_rate==="string"&&(item.display_name===undefined||typeof item.display_name==="string"))):[];
  const stageChanges=Array.isArray(stageRows)?stageRows.filter((item):item is MilestoneTerms=>Boolean(item&&typeof item==="object"&&typeof item.title==="string"&&typeof item.amount==="string"&&(item.id===undefined||typeof item.id==="string"))):[];
  const milestones=[...contract.milestones.map(stage=>stageChanges.find(item=>item.id===stage.id)||stage),...stageChanges.filter(stage=>!stage.id||!contract.milestones.some(item=>item.id===stage.id))];
  const name=(id:string)=>contract.members.find(item=>item.user===id)?.display_name||people.find(person=>(person.user||person.id)===id)?.display_name||"";
  const scalarReady=Boolean(input&&typeof input==="object"&&!Array.isArray(input)&&textReady(terms.scope)&&textReady(terms.revision_terms)&&textReady(terms.expected_duration)&&typeof terms.tracker_required==="boolean"&&numberReady(terms.rate)&&(contract.work_type!=="hourly"||numberReady(terms.weekly_limit)));
  const membersReady=Array.isArray(memberRows)&&members.length===memberRows.length&&members.length>0&&new Set(members.map(item=>item.user)).size===members.length&&members.every(item=>textReady(item.user)&&textReady(name(item.user))&&numberReady(item.hourly_rate));
  const stagesReady=Array.isArray(stageRows)&&stageChanges.length===stageRows.length&&new Set(stageChanges.filter(stage=>stage.id).map(stage=>stage.id)).size===stageChanges.filter(stage=>stage.id).length&&stageChanges.every(item=>textReady(item.title)&&numberReady(item.amount)&&(!item.id||contract.milestones.some(stage=>stage.id===item.id)))&&(contract.work_type!=="fixed"||milestones.length>0);
  const ready=scalarReady&&membersReady&&stagesReady&&inventoryReady;
  const memberIds=Array.from(new Set([...contract.members.map(item=>item.user),...members.map(item=>item.user)]));
  return <article className="card">
    <h3>Koşul değişikliği: mevcut ve önerilen şartlar</h3><Status value={change.status}/>
    <p>Öneride bulunmayan alanlar ve mevcut aşamalar korunur. Kabul, aşağıdaki şartların tümüne uygulanır.</p>
    <div className="table-wrap"><table><thead><tr><th>Şart</th><th>Mevcut</th><th>Önerilen</th></tr></thead><tbody>
      <TermRow label="İş kapsamı" before={contract.scope} after={readableText(terms.scope)||"Şart alınamadı"}/>
      <TermRow label="Revizyon koşulları" before={contract.revision_terms} after={readableText(terms.revision_terms)||"Şart alınamadı"}/>
      <TermRow label="Beklenen süre" before={contract.expected_duration} after={readableText(terms.expected_duration)||"Şart alınamadı"}/>
      <TermRow label="Masaüstü takip" before={contract.tracker_required?"Zorunlu":"Tercihe bağlı"} after={typeof terms.tracker_required==="boolean"?(terms.tracker_required?"Zorunlu":"Tercihe bağlı"):"Şart alınamadı"}/>
      <TermRow label="Sözleşme saatlik ücreti" before={money(contract.rate)} after={numberReady(terms.rate)?money(terms.rate):"Şart alınamadı"}/>
      <TermRow label="Ortak haftalık saat sınırı" before={contract.work_type==="hourly"?`${contract.weekly_limit} saat`:"Uygulanmaz"} after={contract.work_type!=="hourly"?"Uygulanmaz":numberReady(terms.weekly_limit)?`${terms.weekly_limit} saat`:"Şart alınamadı"}/>
    </tbody></table></div>{contract.work_type==="fixed"?<p className="muted">Sabit iş bedeli aşamalardan belirlenir; sözleşme saatlik ücreti ve haftalık sınır sabit işin ödeme hesabına uygulanmaz.</p>:null}
    <h4>İşe dahil öğrenciler ve ayrı saatlik ücretler</h4><div className="table-wrap"><table><thead><tr><th>Öğrenci</th><th>Mevcut ücret</th><th>Önerilen ücret</th><th>Değişiklik</th></tr></thead><tbody>{memberIds.map(id=>{const before=contract.members.find(item=>item.user===id);const after=members.find(item=>item.user===id);return <tr key={id}><th scope="row">{name(id)||"Öğrenci adı henüz alınamadı"}</th><td>{before?`${money(before.hourly_rate)}/saat`:"İşe dahil değil"}</td><td>{after?`${money(after.hourly_rate)}/saat`:"İşten çıkarılması öneriliyor"}</td><td>{!before?"Yeni çalışan":!after?"Çalışan çıkarılıyor":before.hourly_rate===after.hourly_rate?"Değişmiyor":"Ücret değişiyor"}</td></tr>;})}</tbody></table></div>
    <h4>Aşamalar ve iş bedeli</h4>{milestones.length||contract.milestones.length?<div className="table-wrap"><table><thead><tr><th>Aşama</th><th>Mevcut</th><th>Önerilen</th><th>Kaydın durumu</th></tr></thead><tbody>{milestones.map((stage,index)=>{const before=stage.id?contract.milestones.find(item=>item.id===stage.id):undefined;return <tr key={stage.id||`new-${index}`}><th scope="row">{before&&before.title!==stage.title?`${before.title} → ${stage.title}`:stage.title||"Başlık alınamadı"}</th><td>{before?money(before.amount):"Henüz yok"}</td><td>{money(stage.amount)}</td><td>{before?"Mevcut aşama; geçmişi korunur":"Yeni aşama; ayrı ön fonlama gerekir"}</td></tr>;})}</tbody></table></div>:<p>Saatlik sözleşmede sabit aşama yok.</p>}
    {!ready?<Notice tone="warning">Bütün şartlar ve öğrenci adları yüklenmeden kabul açılamaz. Eksik veri varsa sözleşmeyi yenileyin; önerinin düzeltilmesi gerekebilir.</Notice>:null}
    {change.status==="pending"&&canAccept&&change.proposer!==userId?<Action path={`contract-changes/${change.id}/accept/`} label="Gösterilen bütün yeni koşulları kabul et" disabled={!ready||Boolean(change.accepted_by?.includes(userId))} onSuccess={refresh}/>:null}
  </article>;
}
