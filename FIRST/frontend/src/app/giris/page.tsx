import { AuthForm } from '../../components/auth-form';
export default async function Page({searchParams}: {searchParams: Promise<{google_error?: string}>}) {
  const params = await searchParams;
  return <AuthForm googleError={params.google_error}/>;
}
