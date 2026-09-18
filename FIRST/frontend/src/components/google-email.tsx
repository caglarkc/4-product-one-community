'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiError } from '../lib/api';
import { AccountForm } from './account-form';
import { Alert, PageHeading, Surface } from './ui';
export function VerifyGoogleEmail({token}: {token: string}) {
  const router = useRouter();
  return <Surface className="form-page"><PageHeading title="Google girişi için e-postanızı doğrulayın"/>
    {token ? <AccountForm<{status: string}> title="E-posta adresini onayla" path="google/email/verify" extra={{key: token}} submit="Doğrula ve devam et" onSuccess={data => {
      if(!['authenticated', 'profile_required'].includes(data.status)) throw new ApiError('Doğrulama tamamlanamadı. Google girişini yeniden başlatın.', 502);
      router.replace(data.status === 'authenticated' ? '/' : '/kayit/google'); router.refresh();
    }}><p>Bu bağlantıyı Google girişini başlattığınız tarayıcıda açın. Onayladığınızda e-posta adresinizle eşleşen hesabınıza giriş yapılır veya kayıt bilgilerinizi tamamlamaya devam edersiniz.</p></AccountForm>
      : <Alert role="alert" tone="error">Doğrulama bağlantısı eksik veya geçersiz.</Alert>}
    <p><Link href="/kayit/google">Doğrulama bağlantısını yeniden iste</Link> · <Link href="/giris">Google girişini yeniden başlat</Link></p>
  </Surface>;
}
