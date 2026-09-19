import { Alert } from '../../components/ui';
import { AuthForm } from '../../components/auth-form';
export default async function Page({searchParams}: {searchParams: Promise<{google_error?: string; github_error?: string; account_deleted?: string; github_cleanup?: string}>}) {
  const params = await searchParams;
  return <>{params.account_deleted === '1' && <Alert role="status" tone="success"><p>FIRST hesabınız silindi. GitHub hesabınız ve repolarınız korunur.</p>{params.github_cleanup === '1' && <p>GitHub izni otomatik kaldırılamadı. <a href="https://github.com/settings/applications" target="_blank" rel="noopener noreferrer">GitHub ayarlarından kalan izni kaldırın (yeni sekme)</a>.</p>}</Alert>}<AuthForm googleError={params.google_error} githubError={params.github_error}/></>;
}
