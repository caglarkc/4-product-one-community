"use client";
import Link from "next/link";
import { useState } from "react";
import { useSession } from "@/components/session";
import { Action, Auth, Heading, Notice, Panel, Pager, State, Status, TaskForm, usePaged, value, type FieldSpec } from "@/components/ui";
import { date, money, safeExternal } from "@/lib/api";
import { useResource } from "@/lib/hooks";
import type { Money, Payment, Payout } from "@/lib/types";
function buyerFields(required:boolean):FieldSpec[] {return required?[{name:"first_name",label:"Fatura adı",required:true},{name:"last_name",label:"Fatura soyadı",required:true},{name:"phone",label:"Telefon",type:"tel",required:true},{name:"address",label:"Fatura adresi",type:"textarea",required:true},{name:"city",label:"Şehir",required:true},{name:"postal_code",label:"Posta kodu"},{name:"identity_number",label:"Ödeme için T.C. kimlik numarası",type:"password",required:true,autoComplete:"off"}]:[];}
function buyerBody(data:FormData,fields:FieldSpec[]) {return fields.length?{buyer:Object.fromEntries(fields.map(field=>[field.name,value(data,field.name)]))}:{};}
export function PaymentCard({ payment, onUpdate }: { payment:Payment; onUpdate?:(payment:Payment)=>void }) { const {config}=useSession();
  const checkout=safeExternal(payment.checkout_url);
  const billing=buyerFields(config?.payment_requires_buyer===true);
  const simulated=payment.mode==="simulator"&&config?.payment_provider==="simulator"&&config.mode==="test"; return <article className="card">
<div className="meta">
<Status value={payment.mode}/>
<Status value={payment.status}/>
<span>{money(payment.amount)}</span>
</div>
<p className="muted">Ödeme denemesi: {payment.attempt}</p>
<dl>
<dt>Serbest bırakılan</dt>
<dd>{money(payment.released_amount)}</dd>
<dt>İade edilen</dt>
<dd>{money(payment.refunded_amount)}</dd>
<dt>{payment.mode==="simulator"?"Yerel deneme mutabakatı":"Banka aktarımı"}</dt>
<dd>
<Status value={payment.settlement_status}/>
</dd>
</dl>{payment.error_code?<Notice tone="error">Ödeme tamamlanmadı: {payment.error_code}</Notice>:null}{checkout&&["created","pending","unknown"].includes(payment.status)?<p>
<a className="button" href={checkout} target="_blank" rel="noopener noreferrer">Güvenli ödeme sayfasını aç</a>{payment.checkout_expires_at?<small> Geçerlilik: {date(payment.checkout_expires_at)}</small>:null}</p>:null}<div className="actions">
<Action path={`payments/${payment.id}/reconcile/`} label="Ödeme sonucunu kontrol et" message="Ödeme sonucu sunucudan yenilendi." onSuccess={result=>onUpdate?.(result as Payment)}/>{simulated?<>
<Action path={`payments/${payment.id}/simulate/`} body={{outcome:"success"}} label="Yerel denemeyi başarılı sonuçlandır" message="Yerel deneme kaydedildi; sağlayıcı doğrulaması veya gerçek para değildir." onSuccess={result=>onUpdate?.(result as Payment)}/>
<Action path={`payments/${payment.id}/simulate/`} body={{outcome:"failure"}} label="Yerel başarısızlığı dene" message="Yerel başarısızlık kaydedildi." onSuccess={result=>onUpdate?.(result as Payment)}/>
</>:null}</div>{payment.status==="failed"&&payment.retry_allowed===true?<details className="details"><summary>Başarısız ödemeyi yeniden dene</summary><p>Sunucu bu ödeme için yeni denemeye izin verdi. Ödeme tutarı ve hedefi değişmez.</p><TaskForm<Payment> path={`payments/${payment.id}/retry/`} fields={billing} build={data=>buyerBody(data,billing)} clearOnSuccess disabled={!config?.payment_ready} label="Yeni ödeme denemesini başlat" message="Yeni ödeme denemesi oluşturuldu; fonlama doğrulanmış sonuç bekler." onSuccess={result=>onUpdate?.(result)}/></details>:payment.status==="unknown"?<Notice tone="warning">Sonuç bilinmiyor. Yeni tahsilat başlatmadan ödeme sonucunu kontrol edin.</Notice>:null}{payment.mode==="simulator"?<p className="muted">Yerel deneme gerçek sandbox veya canlı sağlayıcı sonucu değildir.</p>:null}</article>; }
export function Funding({ target, disabled, onFunded }: { target:{milestone?:string;week?:string;credit_purchase?:string}; disabled?:boolean; onFunded?:()=>void }) { const {config}=useSession();
  const [payment,setPayment]=useState<Payment|null>(null);
  const available=config?.payment_ready===true;
  const buyerNeeded=config?.payment_requires_buyer===true;
  const billing=buyerFields(buyerNeeded); return <div className="details">{!available?<Notice tone="warning">Ödeme bağlantısı hazır değil. Fonlama başlatılamaz; iş bedeli tahsil edilmiş sayılmaz.</Notice>:null}<TaskForm<Payment> path="payments/" fields={billing} clearOnSuccess build={data=>({...target,...buyerBody(data,billing)})} label="Fonlamayı başlat" message="Ödeme isteği oluşturuldu. Fonlama ödeme sonucu doğrulandığında tamamlanır." disabled={disabled||!available} onSuccess={result=>{setPayment(result);if(result.status==="funded")onFunded?.();}}/>{payment?<PaymentCard payment={payment} onUpdate={result=>{setPayment(result);if(result.status==="funded")onFunded?.();}}/>:null}<p>
<Link href="/money">Ödeme geçmişini aç</Link>
</p>
</div>; }
export function PayoutState({payout}:{payout:Pick<Payout,"mode"|"status"|"bank_transfer_proven">}) {
  if(payout.mode==="simulator")return <span className="status">Yerel çekim denemesi · {payout.status==="paid"?"Başarılı":payout.status==="failed"?"Başarısız":payout.status==="processing"?"İşleniyor":"Bekliyor"}</span>;
  if(payout.status==="paid"&&payout.bank_transfer_proven!==true)return <span className="status">Banka aktarım kanıtı henüz doğrulanmadı</span>;
  return <Status value={payout.status}/>;
}
export function Payments() { const {user,config}=useSession();
  const ledger=useResource<Money>(user?"money/":null);
  const payments=usePaged<Payment>(user?"payments/":null);
  const payouts=usePaged<Payout>(user?"payouts/":null);
  const simulatedPayout=config?.mode==="test"&&config.payment_provider==="simulator";
  return <Auth>
<Heading title="Ödeme ve kazanç" description="Ön fonlama, serbest bırakılan kazanç ve banka aktarımını ayrı takip edin. Çekim talebi banka ödemesi değildir."/>
<State loading={ledger.loading} error={ledger.error} retry={ledger.reload}>{ledger.data?<div className="grid grid-three">
<Panel title="Çekilebilir kazanç">
<p className="metric">{money(ledger.data.available)}</p>
</Panel>
<Panel title="Rezerve tutar">
<p className="metric">{money(ledger.data.reserved)}</p>
<p className="muted">Bekleyen çekim rezervleri bu tutara dahildir.</p>
</Panel>
<Panel title="Bekleyen kazanç">
<p className="metric">{money(ledger.data.pending)}</p>
</Panel>
</div>:null}</State>
<Panel title={simulatedPayout?"Yerel çekim denemesi":"Banka hesabına çekim talebi"}>
{simulatedPayout?<Notice>Bu çekim test bakiyesiyle yerel deneme oluşturur. Gerçek banka aktarımı yapılmaz.</Notice>:null}
<p>Kendi adınıza banka hesabı kullanın. Takım kazancı liderin hesabına aktarılır; iç paylaşımı takım yönetir.</p>{config?.credit_policy.withdraw_minimum==null?<Notice tone="warning">Çekim alt limiti veya sağlayıcı aktarım koşulları henüz yapılandırılmadı. Sunucu hazır olmayan işlemi tamamlanmış göstermez.</Notice>:<p>Alt limit: {money(config.credit_policy.withdraw_minimum)}</p>}{!config?.payout_ready?<Notice tone="warning">Banka çekim bağlantısı henüz hazır değil. Talep şu anda gönderilemez.</Notice>:null}<TaskForm<Payout> path="payouts/" fields={[{name:"amount",label:"Çekmek istediğim tutar (TL)",type:"number",required:true,min:0,step:"0.01"},{name:"account_name",label:"Banka hesabındaki ad soyad",required:true},{name:"iban",label:"Kendi adıma IBAN",required:true,autoComplete:"off"}]} label={simulatedPayout?"Yerel çekim denemesi oluştur":"Çekim talebi gönder"} message={simulatedPayout?"Yerel çekim denemesi kaydedildi; gerçek banka transferi değildir.":"Çekim talebiniz kaydedildi. Banka aktarımını aşağıdaki durumdan takip edin."} disabled={!config?.payout_ready} clearOnSuccess onSuccess={()=>{payouts.reload();ledger.reload();}}/>
</Panel>
<Panel title="Çekim talepleri">
<State loading={payouts.loading} error={payouts.error} empty={!payouts.items.length} retry={payouts.reload}>{payouts.items.map(payout=>
<article className="card" key={payout.id}>
<div className="meta">
<Status value={payout.mode}/>
<PayoutState payout={payout}/>
<span>{money(payout.amount)}</span>
</div>
<p>{payout.account_name} · {payout.iban_masked}</p>
<p className="muted">Talep: {date(payout.requested_at)}{payout.paid_at?` · ${payout.mode==="simulator"?"Yerel deneme sonucu":"Aktarım"}: ${date(payout.paid_at)}`:""}</p>{payout.mode==="simulator"||payout.bank_transfer_proven!==true?<p className="muted">Bu kaydın banka aktarımı kanıtlanmış değildir.</p>:null}{payout.failure_reason?<Notice tone="error">{payout.failure_reason}</Notice>:null}</article>)}<Pager {...payouts}/>
</State>
</Panel>
<Panel title="Ödeme geçmişi">
<State loading={payments.loading} error={payments.error} empty={!payments.items.length} retry={payments.reload}>{payments.items.map(payment=>
<PaymentCard key={payment.id} payment={payment} onUpdate={()=>{payments.reload();ledger.reload();}}/>)}<Pager {...payments}/>
</State>
</Panel>{ledger.data?.entries?.length?<Panel title="Kazanç hareketleri">
<div className="table-wrap">
<table>
<thead>
<tr>
<th>İşlem</th>
<th>Tutar</th>
<th>Tarih</th>
</tr>
</thead>
<tbody>{ledger.data.entries.map(entry=>
<tr key={entry.id}>
<td>{entry.description||entry.reason||entry.kind}</td>
<td>{money(entry.delta??entry.amount)}</td>
<td>{date(entry.created_at)}</td>
</tr>)}</tbody>
</table>
</div>
</Panel>:null}</Auth>; }
