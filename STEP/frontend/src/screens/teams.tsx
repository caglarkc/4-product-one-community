"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "@/components/session";
import { Action, Auth, Heading, Notice, Panel, Pager, State, Status, TaskForm, usePaged, value } from "@/components/ui";
import { useResource, useCollection } from "@/lib/hooks";
import type { Contract, LeaderChange, Team, TeamInvitation } from "@/lib/types";
export function Teams() { const {user}=useSession();
  const router=useRouter();
  const invitations=usePaged<TeamInvitation>(user?"team-invitations/":null);
  const teams=usePaged<Team>(user?"teams/":null); return <Auth>
<Heading title="Takımlarım" description="Takım adına başvuru, sözleşme kabulü ve kazanç çekimi liderdedir."/>
<Panel title="Takım davetlerim">
<State loading={invitations.loading} error={invitations.error} empty={!invitations.items.length} retry={invitations.reload}>{invitations.items.map(invitation=>
<article className="card" key={invitation.id}>
<h3>{invitation.name}</h3>
<p>{invitation.description}</p>
<p>Davet eden lider: {invitation.leader_name}</p>
<div className="actions">
<Action path={`teams/${invitation.id}/membership/`} body={{action:"accept"}} label="Takıma katıl" onSuccess={()=>{invitations.reload();teams.reload();}}/>
<Action path={`teams/${invitation.id}/membership/`} body={{action:"decline"}} label="Daveti reddet" onSuccess={invitations.reload}/>
</div>
</article>)}<Pager {...invitations}/>
</State>
</Panel>
<Panel title="Takım oluştur">
<TaskForm<Team> path="teams/" fields={[{name:"name",label:"Takım adı",required:true},{name:"description",label:"Takım açıklaması",type:"textarea",required:true}]} label="Takımı oluştur" onSuccess={team=>router.push(`/teams/${team.id}`)}/>
</Panel>
<State loading={teams.loading} error={teams.error} empty={!teams.items.length} retry={teams.reload}>
<div className="grid">{teams.items.map(team=>
<Panel key={team.id} title={team.name}>
<p>{team.description}</p>
<p>{team.leader===user?.id?"Takım liderisiniz.":"Takım üyesisiniz."}</p>
<Link href={`/teams/${team.id}`}>Takım alanını aç</Link>
</Panel>)}</div>
<Pager {...teams}/>
</State>
</Auth>; }
export function TeamDetail() { const {id}=useParams<{id:string}>();
  const {user}=useSession();
  const team=useResource<Team>(user?`teams/${id}/`:null);
  const contracts=useCollection<Contract>(user?"contracts/":null);
  const changes=usePaged<LeaderChange>(user?"leader-changes/":null);
  const leader=team.data?.leader===user?.id;
  const active=contracts.items.filter(contract=>contract.team===id&&contract.status==="active"); return <Auth>
<State loading={team.loading} error={team.error} retry={team.reload}>{team.data?<>
<Heading title={team.data.name} description={team.data.description}/>
<Panel title="Üyeler">
<ul>{team.data.members.map(member=>
<li key={member.user}>{member.display_name} <Status value={member.status}/>{member.user===team.data?.leader?" · Lider":""}</li>)}</ul>{team.data.members.some(member=>member.user===user?.id&&member.status==="invited")?<div className="actions">
<Action path={`teams/${id}/membership/`} body={{action:"accept"}} label="Takım davetini kabul et" onSuccess={team.reload}/>
<Action path={`teams/${id}/membership/`} body={{action:"decline"}} label="Daveti reddet" onSuccess={team.reload}/>
</div>:<Action path={`teams/${id}/membership/`} body={{action:"leave"}} label="Takımdan ayrıl" disabled={leader} message="Üyelik işlemi kaydedildi; aktif sözleşme yetkileri ayrı korunur." onSuccess={team.reload}/>}<Link href="/credits">Ayrı takım kredi hesabına git</Link>
</Panel>{leader?<>
<Panel title="Takımı düzenle">
<TaskForm path={`teams/${id}/`} method="PATCH" fields={[{name:"name",label:"Takım adı",required:true,value:team.data.name},{name:"description",label:"Açıklama",type:"textarea",required:true,value:team.data.description}]} label="Takımı güncelle" onSuccess={team.reload}/>
</Panel>
<Panel title="Üye davet et">
<TaskForm path={`teams/${id}/invite/`} fields={[{name:"email",label:"Üyenin STEP e-posta adresi",type:"email",required:true}]} label="Takıma davet et" message="Takım daveti gönderildi. Üyelik kişinin kabulüyle başlar." onSuccess={team.reload}/>
</Panel>
<Panel title="Lider değişikliği">
<Notice>Aktif işlerde işveren ve yönetim onayı gerekir. Mevcut işlerin ödeme alıcısı ayrıca açıkça seçilir; lider değişmesi kazanç alıcısını kendiliğinden değiştirmez.</Notice>{contracts.error?<Notice tone="error">Aktif sözleşmeler yüklenemedi: {contracts.error}</Notice>:null}<p className="muted">{contracts.loading?"Aktif sözleşmeler yükleniyor…":`${active.length} aktif sözleşmenin ödeme alıcısı bu öneride açıkça belirlenir.`}</p>
<TaskForm path={`teams/${id}/leader-change/`} fields={[{name:"new_leader",label:"Yeni lider",type:"select",required:true,options:team.data.members.filter(member=>member.status==="accepted"||member.status==="active").map(member=>({value:member.user,label:member.display_name}))},{name:"payee",label:"Mevcut işlerin ödeme alıcısı",type:"select",required:true,options:team.data.members.map(member=>({value:member.user,label:member.display_name}))},{name:"reason",label:"Değişiklik gerekçesi",type:"textarea",required:true}]} build={data=>({new_leader:value(data,"new_leader"),payee:value(data,"payee"),reason:value(data,"reason"),contract_ids:active.map(contract=>contract.id)})} label="Lider değişikliği öner" disabled={contracts.loading||Boolean(contracts.error)} message="Lider değişikliği onay sürecine gönderildi." onSuccess={()=>{team.reload();changes.reload();}}/>
</Panel>
</>:null}<Panel title="Lider değişikliği talepleri">
<State loading={changes.loading} error={changes.error} retry={changes.reload}>{changes.items.filter(change=>change.team===id).map(change=>
<article className="card" key={change.id}>
<Status value={change.status}/>
<p>{change.reason}</p>
<p>Yeni lider: {change.new_leader_name||"Seçilen üye"} · Ödeme alıcısı: {change.payee_name||"Seçilen üye"}</p>
<p className="muted">Yönetim onayı: {change.admin_approved?"Tamamlandı":"Bekliyor"}</p>
</article>)}<Pager {...changes}/>
</State>
</Panel>
</>:null}</State>
</Auth>; }
