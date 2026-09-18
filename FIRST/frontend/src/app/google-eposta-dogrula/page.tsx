import { VerifyGoogleEmail } from '../../components/google-email';
export default async function Page({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
  const query = await searchParams;
  return <VerifyGoogleEmail token={typeof query.key === 'string' ? query.key : ''}/>;
}
