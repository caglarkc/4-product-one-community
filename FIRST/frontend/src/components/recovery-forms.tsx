'use client';
import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, User } from '../lib/api';
import { AccountForm } from './account-form';
import { EmailReminder } from './account-status';

export function ForgotPassword() {
  return <section className="card"><h1>Şifremi unuttum</h1>
    <AccountForm title="Sıfırlama bağlantısı iste" path="password/reset" fields={[{name: 'email', label: 'E-posta', type: 'email', maxLength: 254}]} submit="Sıfırlama bağlantısı gönder">
      <p>Hesap uygunsa e-posta gönderilir. Bağlantı 30 dakika geçerlidir.</p>
    </AccountForm><Link href="/giris">Girişe dön</Link>
  </section>;
}
export function ResetPassword({uid, token}: {uid: string; token: string}) {
  const router = useRouter();
  return <section className="card"><h1>Şifre sıfırla</h1>
    {uid && token ? <AccountForm title="Yeni şifre belirle" path="password/reset/confirm" extra={{uid, token}}
      fields={[{name: 'password', label: 'Yeni şifre', type: 'password', password: true}]} submit="Şifreyi sıfırla"
      onSuccess={() => {router.replace('/giris'); router.refresh();}}>
      <p>Başarıyla sıfırlandıktan sonra bütün oturumlar kapanır; yeni şifrenizle giriş yapın.</p>
    </AccountForm> : <p role="alert">Sıfırlama bağlantısı eksik veya geçersiz.</p>}
    <p><Link href="/sifremi-unuttum">Bağlantı geçersiz veya süresi dolduysa yeni bağlantı iste</Link></p>
  </section>;
}
export function VerifyEmail({token}: {token: string}) {
  const [confirmed, setConfirmed] = useState(false);
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [sessionError, setSessionError] = useState('');
  async function refreshSession() {
    setSessionError('');
    try {setUser((await api<{user: User | null}>('me')).user);}
    catch (caught) {setSessionError((caught as Error).message);}
  }
  return <section className="card"><h1>E-posta doğrula</h1>
    {!confirmed && (token ? <AccountForm title="Adresi onayla" path="email/verify" extra={{key: token}} submit="E-posta adresini onayla"
      onSuccess={async () => {setConfirmed(true); await refreshSession();}}>
      <p>Bu bağlantıyı açmak hesabınızı değiştirmez. E-posta adresinizi doğrulamak için onaylayın. Adres değişikliğinde bütün oturumlar kapanır.</p>
    </AccountForm> : <p role="alert">Doğrulama bağlantısı eksik veya geçersiz.</p>)}
    {confirmed && <><p role="status">E-posta adresi doğrulandı.</p>
      {user === undefined && !sessionError && <p role="status">Oturum kontrol ediliyor…</p>}
      {user === null && <p>Oturumunuz açık değil. <Link href="/giris">Giriş yapın</Link>.</p>}
      {user && <p><Link href="/hesap">Hesabıma dön</Link></p>}
      {sessionError && <div role="alert"><p>{sessionError}</p><button onClick={refreshSession}>Oturumu yeniden kontrol et</button></div>}
    </>}
    {!confirmed && <><p>Bağlantınız geçersiz veya süresi dolmuşsa giriş yapıp doğrulama e-postasını yeniden isteyebilirsiniz. Yeni adres değişikliği için hesabınızdan yeniden değişiklik isteği gönderin.</p>
      <EmailReminder reminder={false}/><p><Link href="/giris">Giriş yap</Link> · <Link href="/hesap">E-posta değişikliği iste</Link></p></>}
  </section>;
}
