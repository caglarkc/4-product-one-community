import type {PageInfo} from './community';
export type DirectMessage={id:string;sender_username:string;body:string;created_at:string;is_mine?:boolean};
export type Conversation={id:string;participant:{username:string;full_name:string;avatar_url:string};last_message:DirectMessage|null;unread_count:number;can_message:boolean;updated_at:string};
export type InboxPage=PageInfo&{conversations:Conversation[]};
export type ConversationPage={conversation:Conversation;messages:DirectMessage[];next_before:string|null};
