import {PublicProfilePage} from '../../../components/people';
export default async function Page({params}:{params:Promise<{username:string}>}){const {username}=await params;return <PublicProfilePage username={username}/>;}
