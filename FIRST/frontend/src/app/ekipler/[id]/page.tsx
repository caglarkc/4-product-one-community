import {TeamDetailPage} from '../../../components/teams';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <TeamDetailPage id={id}/>;}
