import {MessagesPage} from '../../components/messages';
export default async function Page({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}){const query=await searchParams;return <MessagesPage initialUsername={typeof query.username==='string'?query.username:''}/>;}
