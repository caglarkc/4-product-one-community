import {redirect} from 'next/navigation';
import {ProjectEditor} from '../../../components/projects';
export default async function Page({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
 const query = await searchParams;
 if (query.github_setup === '1') redirect('/github-kurulum?github_setup=1');
 return <ProjectEditor/>;
}
