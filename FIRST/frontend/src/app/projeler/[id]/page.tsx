import {ProjectDetail} from '../../../components/projects';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <ProjectDetail id={id}/>;}
