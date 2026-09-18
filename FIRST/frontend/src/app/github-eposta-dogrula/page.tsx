import { VerifySocialEmail } from '../../components/social-email';
export default async function Page({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
 const query = await searchParams;
 return <VerifySocialEmail provider="github" token={typeof query.key === 'string' ? query.key : ''}/>;
}
