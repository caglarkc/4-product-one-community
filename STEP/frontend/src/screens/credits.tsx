"use client";
import { useState } from "react";
import { useSession } from "@/components/session";
import { Auth, Heading, Notice, Panel, Pager, State, Status, TaskForm, usePaged, value } from "@/components/ui";
import { date, money } from "@/lib/api";
import { useResource, useCollection } from "@/lib/hooks";
import type { Case, CreditPurchase, CreditWallet, Team } from "@/lib/types";
import { Funding } from "./payments";
export function Credits() { const {user,config}=useSession();
  const [team,setTeam]=useState("");
  const [purchase,setPurchase]=useState<CreditPurchase|null>(null);
  const teams=useCollection<Team>(user?"teams/":null);
  const wallet=useResource<CreditWallet>(user?`credits/${team?`?team=${team}`:""}`:null);
  const purchases=usePaged<CreditPurchase>(user?"credit-purchases/":null);
  const refunds=usePaged<Case>(user?"credit-refunds/":null);
  const leader=!team||teams.items.find(item=>item.id===team)?.leader===user?.id;
  const price=config?.credit_policy.credit_price;
  return <Auth>
<Heading title="Krediler" description="Kredi ilan, başvuru ve öne çıkarma içindir. İş bedelini fonlamaz. Ücretsiz ve satın alınan bütün krediler süresizdir."/>
<Panel title="Kredi hesabı">
<label className="field">Gösterilecek hesap<select disabled={teams.loading||Boolean(teams.error)} value={team} onChange={event=>{setTeam(event.target.value);setPurchase(null);}}>
<option value="">Kişisel hesabım</option>{teams.items.map(item=>
<option value={item.id} key={item.id}>{item.name}</option>)}</select>
</label>
<State loading={teams.loading} error={teams.error} retry={teams.reload}><p className="muted">Takım hesapları bütün sayfalardan yüklendi.</p></State>
<State loading={wallet.loading} error={wallet.error} retry={wallet.reload}>{wallet.data?<>
<p className="metric">{wallet.data.balance} kredi</p>
<Status value={wallet.data.mode}/>{!leader?<Notice>Takım kredisini yalnız lider harcayabilir.</Notice>:null}<div className="table-wrap">
<table>
<thead>
<tr>
<th>İşlem</th>
<th>Kredi</th>
<th>Son bakiye</th>
<th>Tarih</th>
</tr>
</thead>
<tbody>{wallet.data.entries.map(entry=>
<tr key={entry.id}>
<td>{entry.description||entry.kind||entry.reason}</td>
<td>{entry.delta??entry.amount}</td>
<td>{entry.balance_after??entry.balance}</td>
<td>{date(entry.created_at)}</td>
</tr>)}</tbody>
</table>
</div>
</>:null}</State>
</Panel>
<Panel title="Kredi satın al">{price==null?<Notice tone="warning">Kredi satış fiyatı henüz belirlenmedi. Satın alma başlatılamaz.</Notice>:<p>Birim kredi fiyatı: {money(price)}. Ödeme tutarı sunucu tarafından belirlenir.</p>}<TaskForm<CreditPurchase> path="credit-purchases/" fields={[{name:"credits",label:"Satın almak istediğim kredi",type:"number",required:true,min:1,step:"1"}]} build={data=>({credits:Number(value(data,"credits")),...(team?{team}: {})})} label="Satın alma isteği oluştur" message="Satın alma isteği oluşturuldu. Kredi, ödeme doğrulandıktan sonra eklenir." disabled={teams.loading||Boolean(teams.error)||wallet.loading||Boolean(wallet.error)||!leader||price==null||!config?.payment_ready} onSuccess={result=>{setPurchase(result);purchases.reload();}}/>{purchase?<Funding target={{credit_purchase:purchase.id}} onFunded={()=>{wallet.reload();purchases.reload();}}/>:null}</Panel>
<Panel title="Satın almalar ve iade talebi">
<State loading={purchases.loading} error={purchases.error} empty={!purchases.items.length} retry={purchases.reload}>{purchases.items.map(item=>
<article className="card" key={item.id}>
<div className="meta">
<span>{item.credits} kredi</span>
<span>{money(item.amount)}</span>
<Status value={item.status}/>
</div>{["pending","created"].includes(item.status)?<Funding target={{credit_purchase:item.id}} onFunded={()=>{wallet.reload();purchases.reload();}}/>:null}<details className="details">
<summary>Kullanılmamış kredi için iade iste</summary>
<TaskForm path="credit-refunds/" fields={[{name:"reason",label:"İade gerekçesi",type:"textarea",required:true}]} build={data=>({purchase:item.id,reason:value(data,"reason")})} label="İade talebi gönder" message="İade talebi incelemeye gönderildi. Otomatik para iadesi değildir." onSuccess={refunds.reload}/>
</details>
</article>)}<Pager {...purchases}/>
</State>
</Panel>
<Panel title="İade taleplerim">
<State loading={refunds.loading} error={refunds.error} empty={!refunds.items.length} retry={refunds.reload}>{refunds.items.map(item=>
<article className="card" key={item.id}>
<Status value={item.status}/>
<p>{item.reason}</p>
</article>)}<Pager {...refunds}/>
</State>
</Panel>
<Panel title="Ücretsiz haklar">
<p>Başlangıç ve aylık krediler öğrenci ve işveren için ayrı yapılandırılır. Önceki bakiyeniz aylık dağıtımda silinmez.</p>
<p className="muted">Öğrenci: başlangıç {config?.credit_policy.initial_student==null?"belirlenmedi":String(config.credit_policy.initial_student)}, aylık {config?.credit_policy.monthly_student==null?"belirlenmedi":String(config.credit_policy.monthly_student)}. İşveren: başlangıç {config?.credit_policy.initial_employer==null?"belirlenmedi":String(config.credit_policy.initial_employer)}, aylık {config?.credit_policy.monthly_employer==null?"belirlenmedi":String(config.credit_policy.monthly_employer)}.</p>
</Panel>
</Auth>;
}
