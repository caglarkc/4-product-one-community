'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, User } from '../lib/api';
import { RequireSession, useSession } from './session-provider';
import { AccountReset } from './account-reset';
import { ConnectedAccounts } from './connected-accounts';
import { AccountForm, Field, ReauthenticationContext } from './account-form';
import { ActionLink, Alert, Button, PageHeading } from './ui';

type Session = {id: string; created_at: string; expires_at: string; current: boolean};
export function EmailReminder({reminder = true}: {reminder?: boolean}) {
  return <aside className="email-reminder">{reminder && <p>E-posta adresiniz henüz doğrulanmadı.</p>}
    <AccountForm title="E-posta doğrulama" path="email/resend" variant="secondary" submit="Doğrulama e-postasını yeniden gönder">
      <p>Bağlantı 24 saat geçerlidir. Gönderimler arasında 60 saniye bekleyin; saatte en fazla 5 gönderim yapılabilir.</p>
    </AccountForm></aside>;
}
export function SessionList({onSignedOut}: {onSignedOut: () => void}) {
  const [sessions, setSessions] = useState<Session[] | null>(null);
  const [error, setError] = useState('');
  async function reload() {
    setError('');
    try {setSessions((await api<{sessions: Session[]}>('sessions')).sessions);}
    catch (caught) {setError((caught as Error).message);}
  }
  useEffect(() => { let active = true;
    api<{sessions: Session[]}>('sessions').then(data => {if (active) setSessions(data.sessions);})
      .catch(caught => {if (active) setError(caught.message);});
    return () => {active = false;};
  }, []);
  return <section className="sessions"><h2>Açık oturumlar</h2>
    {error && <Alert role="alert" tone="error"><p>{error}</p><Button onClick={reload}>Oturumları yeniden yükle</Button></Alert>}
    {!sessions && !error && <Alert role="status">Oturumlar yükleniyor…</Alert>}
    {sessions?.length === 0 && <p>Açık oturum bulunamadı.</p>}
    <div className="session-grid">{sessions?.map(session => <AccountForm key={session.id} title={session.current ? 'Bu oturum' : 'Diğer oturum'}
      variant="secondary" path={`sessions/${session.id}`} method="DELETE" submit={session.current ? 'Bu oturumu kapat' : 'Oturumu kapat'}
      onSuccess={async () => {if (session.current) onSignedOut(); else await reload();}}>
      <p>Açılış: <time dateTime={session.created_at}>{new Date(session.created_at).toLocaleString('tr-TR')}</time><br/>Bitiş: <time dateTime={session.expires_at}>{new Date(session.expires_at).toLocaleString('tr-TR')}</time></p>
    </AccountForm>)}</div>
    <AccountForm title="Bütün oturumlar" variant="danger" path="sessions/revoke" submit="Bütün oturumları kapat" onSuccess={onSignedOut}>
      <p>Bu oturum dahil bütün cihazlardan çıkış yapılır.</p>
    </AccountForm>
  </section>;
}
function AccountContent() {
  const router = useRouter();
  const {user, updateUser} = useSession();
  const [sessionRevision, setSessionRevision] = useState(0);
  if(!user) return null;
  function signedOut() {updateUser(null); router.replace('/giris'); router.refresh();}
  const fields: Field[] = [
    {name: 'full_name', label: 'Ad soyad', value: user.full_name, maxLength: 150},
    {name: 'username', label: 'Kullanıcı adı', value: user.username},
    {name: 'birth_date', label: 'Doğum tarihi', type: 'date', value: user.birth_date || ''},
    {name: 'gender', label: 'Cinsiyet', value: user.gender, options: [['female', 'Kadın'], ['male', 'Erkek'], ['other', 'Diğer'], ['unspecified', 'Belirtmek istemiyorum']]},
    {name: 'phone', label: 'Telefon (isteğe bağlı)', type: 'tel', value: user.phone, optional: true, maxLength: 32},
  ];
  return <ReauthenticationContext.Provider value={{google: !!user.providers?.includes('google'), password: user.has_usable_password !== false}}><div className="account-page">
    <PageHeading title="Hesabım" description="Profilinizi, bağlantılarınızı ve güvenlik ayarlarınızı tek yerden yönetin."/>
    <div className="account-summary"><p>{user.full_name || user.username}</p><p className="account-email">{user.email} · {user.email_verified ? 'Doğrulandı' : 'Doğrulama bekliyor'}</p></div>
    <nav className="section-nav" aria-label="Hesap bölümleri"><a href="#profil">Profil</a><a href="#baglantilar">Bağlantılar</a><a href="#guvenlik">Güvenlik</a><a href="#oturumlar">Oturumlar</a><a href="#hesap-islemleri">Hesap işlemleri</a></nav>
    {!user.email_verified && <EmailReminder/>}
    <div className="account-grid"><div className="account-column">
      <div id="profil"><AccountForm<{user: User}> requireChanges title="Profil bilgileri" path="profile" method="PATCH" fields={fields} submit="Değişiklikleri kaydet" onSuccess={data => updateUser(data.user)}>
        <p>Kullanıcı adınız 3–30 harf, rakam veya alt çizgi içerebilir. En az 13 yaşında olmalısınız. Telefon eklerseniz ülke koduyla birlikte yazın; telefon doğrulaması henüz sunulmuyor.</p>
      </AccountForm></div>
      <div id="baglantilar"><ConnectedAccounts user={user}/></div>
    </div><section className="account-column" id="guvenlik" aria-labelledby="security-title"><h2 id="security-title">Giriş ve güvenlik</h2>
      <AccountForm title="E-posta adresi" path="email/change" fields={[{name: 'email', label: 'Yeni e-posta', type: 'email', maxLength: 254}]} submit="Doğrulama bağlantısı gönder">
        <p>Yeni adres doğrulanana kadar {user.email} geçerlidir. Eski adresinize bildirim gönderilir; değişiklik onaylandığında tüm oturumlardan çıkış yapılır.</p>
      </AccountForm>
      {user.has_usable_password !== false ? <AccountForm title="Şifre" path="password/change" fields={[{name: 'old_password', label: 'Mevcut şifre', type: 'password'}, {name: 'password', label: 'Yeni şifre', type: 'password', password: true}]} submit="Şifreyi değiştir" onSuccess={signedOut}>
        <p>Şifreniz değiştiğinde tüm oturumlar kapanır. Yeni şifrenizle yeniden giriş yapabilirsiniz.</p>
      </AccountForm> : <div className="surface account-section"><h2>Şifre ile giriş</h2><p>E-posta adresinize gönderilen bağlantıyla hesabınıza bir şifre ekleyebilirsiniz.</p><ActionLink href="/sifremi-unuttum" variant="secondary">Şifre oluştur</ActionLink></div>}
    </section></div>
    <div id="oturumlar"><SessionList key={sessionRevision} onSignedOut={signedOut}/></div>
    <div id="hesap-islemleri"><AccountReset user={user} onChanged={updated => {updateUser(updated); setSessionRevision(value => value + 1);}} onDeleted={result => {updateUser(null); router.replace(`/giris?account_deleted=1${result.github_cleanup_required ? '&github_cleanup=1' : ''}`); router.refresh();}}/></div>
  </div></ReauthenticationContext.Provider>;
}
// Keep the former profile prop accepted for existing callers.
export const AccountStatus: React.ComponentType<{profile?: boolean}> = () => {
  return <RequireSession><AccountContent/></RequireSession>;
};
