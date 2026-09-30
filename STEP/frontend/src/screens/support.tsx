"use client";
import Link from "next/link";
import { useSession } from "@/components/session";
import { Auth, Heading, Notice, Panel, Pager, State, Status, usePaged } from "@/components/ui";
import { date } from "@/lib/api";
import type { Case, Dispute } from "@/lib/types";
export function Support() {const {user}=useSession();
  const disputes=usePaged<Dispute>(user?"disputes/":null);
  const refunds=usePaged<Case>(user?"credit-refunds/":null);
  return <Auth>
<Heading title="Destek ve incelemeler" description="İş bedeli itirazı ve kredi iadesi ayrı süreçlerde incelenir."/>
<div className="grid">
<Panel title="İş bedeli veya teslim itirazı">
<p>İlgili sözleşmede aşama veya haftayı seçip itiraz açın. Uyuşmazlık çözülene kadar ilgili ödeme bekler.</p>
<Link href="/contracts">Sözleşmelerimi aç</Link>
</Panel>
<Panel title="Kişisel bilgi içeren görüntü">
<p>Çalışma günlüğünüzden görüntüyü işveren görmeden moderasyona gönderin. Görüntü bütün işveren kanallarına kapanır.</p>
<Link href="/contracts">Çalışma günlüğüne git</Link>
</Panel>
</div>
<Panel title="İtirazlarım">
<State loading={disputes.loading} error={disputes.error} empty={!disputes.items.length} retry={disputes.reload}>{disputes.items.map(item=>
<article className="card" key={item.id}>
<Status value={item.status}/>
<p>{item.reason}</p>{item.resolution?<p>Sonuç: {item.resolution}</p>:null}<p className="muted">{date(item.created_at)}</p>
<Link href={`/contracts/${item.contract}`}>İlgili sözleşmeyi aç</Link>
</article>)}<Pager {...disputes}/>
</State>
</Panel>
<Panel title="Kredi iade taleplerim">
<State loading={refunds.loading} error={refunds.error} empty={!refunds.items.length} retry={refunds.reload}>{refunds.items.map(item=>
<article className="card" key={item.id}>
<Status value={item.status}/>
<p>{item.reason}</p>
</article>)}<Pager {...refunds}/>
</State>
<Link href="/credits">Satın alma iade talebi oluştur</Link>
</Panel>
<Notice>İlan şikâyetini ilan detayından gönderin. Açık itirazın ilgili takip kanıtları süreç sonuçlanana kadar korunur.</Notice>
</Auth>;}
