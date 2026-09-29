import {VerifyStudentEmail} from '../../components/profile-extension';
export default async function Page({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}){const query=await searchParams;return <VerifyStudentEmail token={typeof query.key==='string'?query.key:''}/>;}
