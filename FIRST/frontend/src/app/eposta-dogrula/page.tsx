import { VerifyEmail } from '../../components/recovery-forms';
export default async function Page({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
  const query = await searchParams;
  return <VerifyEmail token={typeof query.key === 'string' ? query.key : ''}/>;
}
