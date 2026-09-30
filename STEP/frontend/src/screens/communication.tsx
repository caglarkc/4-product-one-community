"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useSession } from "@/components/session";
import { Action, Auth, Download, FilePicker, Heading, Panel, Pager, State, TaskForm, usePaged, value } from "@/components/ui";
import { date } from "@/lib/api";
import { useResource } from "@/lib/hooks";
import type { Attachment, Conversation, Message, Notice } from "@/lib/types";
export function Messages() { const {user}=useSession();
  const conversations=usePaged<Conversation>(user?"conversations/":null);
  return <Auth>
<Heading title="Mesajlar" description="Görüşmeler başvuru, davet veya sözleşme ilişkisiyle açılır. Dosyalar ilgili görüşmeye özeldir."/>
<State loading={conversations.loading} error={conversations.error} empty={!conversations.items.length} retry={conversations.reload}>{conversations.items.map(conversation=>
<article className="card" key={conversation.id}>
<h2>
<Link href={`/messages/${conversation.id}`}>{conversation.title||"İş görüşmesi"}</Link>
</h2>
<p>{conversation.participants?.map(person=>person.display_name).join(" · ")}</p>
</article>)}<Pager {...conversations}/>
</State>
</Auth>;}
export function ConversationDetail() { const {id}=useParams<{id:string}>();
  const {user}=useSession();
  const conversation=useResource<Conversation>(user?`conversations/${id}/`:null);
  const messages=usePaged<Message>(user?`conversations/${id}/messages/`:null);
  const [attachments,setAttachments]=useState<Attachment[]>([]); const [pickerRevision,setPickerRevision]=useState(0);
  return <Auth>
<State loading={conversation.loading} error={conversation.error} retry={conversation.reload}>
<Heading title={conversation.data?.title||"İş görüşmesi"} description={conversation.data?.participants?.map(person=>person.display_name).join(" · ")} action={conversation.data?.contract?<Link href={`/contracts/${conversation.data.contract}`}>Sözleşme alanı</Link>:undefined}/>
</State>
<Panel title="Görüşme">
<State loading={messages.loading} error={messages.error} empty={!messages.items.length} retry={messages.reload}>{messages.items.map(message=>
<article className="message" key={message.id}>
<div className="meta">
<strong>{message.sender_name||(message.sender===user?.id?"Siz":"Görüşme tarafı")}</strong>
<time>{date(message.created_at)}</time>
</div>
<p>{message.text}</p>{message.attachments?.map(file=>
<Download key={file.id} attachment={file}/>)}</article>)}<Pager {...messages}/>
</State>
</Panel>
<Panel title="Mesaj gönder">
<TaskForm path={`conversations/${id}/messages/`} fields={[{name:"text",label:"Mesaj",type:"textarea",required:true}]} build={data=>({text:value(data,"text"),attachment_ids:attachments.map(file=>file.id)})} label="Mesajı gönder" clearOnSuccess message="Mesaj gönderildi." onSuccess={()=>{setAttachments([]);setPickerRevision(value=>value+1);messages.reload();}}>
<FilePicker key={pickerRevision} scope={{conversation:id}} onChange={setAttachments}/>
</TaskForm>
</Panel>
</Auth>;}
function destination(notice:Notice) { const kind=notice.resource_type;
  const id=notice.resource_id;if(!id)return null;if(kind==="job")return `/jobs/${id}`;if(kind==="contract")return `/contracts/${id}`;if(kind==="conversation")return `/messages/${id}`;if(kind==="payment"||kind==="payout")return "/money";if(kind==="dispute"||kind==="privacy_request")return "/support";if(kind==="application"||kind==="invitation")return "/applications";if(kind==="team"||kind==="leader_change")return "/teams";
  return null;}
export function Notifications() {const {user}=useSession();
  const notifications=usePaged<Notice>(user?"notifications/":null);
  return <Auth>
<Heading title="Bildirimler" description="Teklif, ödeme, teslim ve itiraz hareketlerini takip edin." action={<Link href="/account">Bildirim tercihleri</Link>}/>
<State loading={notifications.loading} error={notifications.error} empty={!notifications.items.length} retry={notifications.reload}>{notifications.items.map(notice=>
<article className="card" key={notice.id}>
<h2>{notice.title}</h2>
<p>{notice.body||notice.message}</p>
<div className="meta">
<time>{date(notice.created_at)}</time>
<span>{notice.read_at?"Okundu":"Yeni"}</span>
</div>
<div className="actions">{destination(notice)?<Link href={destination(notice)!}>İlgili alanı aç</Link>:null}{!notice.read_at?<Action path={`notifications/${notice.id}/read/`} label="Okundu işaretle" onSuccess={notifications.reload}/>:null}</div>
</article>)}<Pager {...notifications}/>
</State>
</Auth>;}
