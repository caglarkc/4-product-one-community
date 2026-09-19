'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiError, oauthDestination } from '../lib/api';
import { AccountForm } from './account-form';
import { Alert, PageHeading, Surface } from './ui';
export function VerifySocialEmail({token, provider}: {token: string; provider: 'google' | 'github'}) {
  const label = provider === 'google' ? 'Google' : 'GitHub';
  const router = useRouter();
  return <Surface className="form-page"><PageHeading title={`${label} girişi için e-postanızı doğrulayın`}/>
    {token ? <AccountForm<{status: string; redirect_to:string}> title="E-posta adresini onayla" path={`${provider}/email/verify`} extra={{key: token}} submit="Doğrula ve devam et" onSuccess={data => {
      if(!['authenticated', 'profile_required'].includes(data.status)) throw new ApiError(`Doğrulama tamamlanamadı. ${label} girişini yeniden başlatın.`, 502);
      router.replace(oauthDestination(data.redirect_to)); router.refresh();
    }}><p>Bu bağlantıyı {label} girişini başlattığınız tarayıcıda açın. Onayladığınızda e-posta adresinizle eşleşen hesabınıza giriş yapılır veya kayıt bilgilerinizi tamamlamaya devam edersiniz.</p></AccountForm>
      : <Alert role="alert" tone="error">Doğrulama bağlantısı eksik veya geçersiz.</Alert>}
    <p><Link href={`/kayit/${provider}`}>Doğrulama bağlantısını yeniden iste</Link> · <Link href="/giris">{label} girişini yeniden başlat</Link></p>
  </Surface>;
}
