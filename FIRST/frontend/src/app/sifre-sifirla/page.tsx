import { ResetPassword } from '../../components/recovery-forms';
export default async function Page({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
  const query = await searchParams;
  return <ResetPassword uid={typeof query.uid === 'string' ? query.uid : ''} token={typeof query.token === 'string' ? query.token : ''}/>;
}
