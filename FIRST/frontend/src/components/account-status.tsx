'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, User } from '../lib/api';
import { AccountForm, Field } from './account-form';
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
    {error && <Alert role="alert" tone="error"><p>{error}</p><Button onClick={reload}>Oturumları yeniden yükle</Button><p><Link href="/giris">Giriş yap</Link></p></Alert>}
    {!sessions && !error && <Alert role="status">Oturumlar yükleniyor…</Alert>}
    {sessions?.length === 0 && <p>Açık oturum bulunamadı.</p>}
    <div className="session-grid">{sessions?.map(session => <AccountForm key={session.id} title={session.current ? 'Bu oturum' : 'Diğer oturum'}
      variant="secondary" path={`sessions/${session.id}`} method="DELETE" submit={session.current ? 'Bu oturumu kapat' : 'Oturumu kapat'}
      onSuccess={async () => {if (session.current) onSignedOut(); else await reload();}}>
      <p>Açılış: <time dateTime={session.created_at}>{session.created_at}</time><br/>Bitiş: <time dateTime={session.expires_at}>{session.expires_at}</time></p>
    </AccountForm>)}</div>
    <AccountForm title="Bütün oturumlar" variant="danger" path="sessions/revoke" submit="Bütün oturumları kapat" onSuccess={onSignedOut}>
      <p>Bu oturum dahil bütün cihazlardan çıkış yapılır.</p>
    </AccountForm>
  </section>;
}
export function AccountStatus({profile = false}: {profile?: boolean}) {
  const router = useRouter();
  const lock = useRef(false);
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {let active = true;
    api<{user: User | null}>('me').then(data => {if (active) setUser(data.user);}).catch(caught => {if (active) setError(caught.message);});
    return () => {active = false;};
  }, []);
  function signedOut() {setUser(null); router.replace('/giris'); router.refresh();}
  const fields: Field[] = user ? [
    {name: 'full_name', label: 'Ad soyad', value: user.full_name, maxLength: 150},
    {name: 'username', label: 'Kullanıcı adı', value: user.username},
    {name: 'birth_date', label: 'Doğum tarihi', type: 'date', value: user.birth_date || ''},
    {name: 'gender', label: 'Cinsiyet', value: user.gender, options: [['female', 'Kadın'], ['male', 'Erkek'], ['other', 'Diğer'], ['unspecified', 'Belirtmek istemiyorum']]},
    {name: 'phone', label: 'Telefon (isteğe bağlı, doğrulanmaz)', type: 'tel', value: user.phone, optional: true, maxLength: 32},
  ] : [];
  return <div className={profile ? "account-page" : "surface home-page"}><PageHeading title={profile ? 'Hesabım' : 'Ana sayfa'} description={profile ? 'Profilinizi, giriş bilgilerinizi ve açık oturumlarınızı yönetin.' : undefined} />
    {error && <Alert role="alert" tone="error"><p>{error}</p>{user === undefined && <Button onClick={() => {setError(''); api<{user: User | null}>('me').then(data => setUser(data.user)).catch(caught => setError(caught.message));}}>Yeniden dene</Button>}</Alert>}
    {user === undefined && !error && <Alert role="status">Oturum kontrol ediliyor…</Alert>}
    {user === null && <Alert><p>Oturumunuz açık değil. <Link href="/giris">Giriş yapın</Link>.</p></Alert>}
    {user && <><div className="account-summary"><p>Merhaba, {user.full_name}.</p>
      {profile && <p className="account-email">E-posta: {user.email} — {user.email_verified ? 'Doğrulandı' : 'Doğrulanmadı'}</p>}</div>
      {!user.email_verified && <EmailReminder/>}
      {!profile && <div className="home-actions"><ActionLink href="/hesap">Hesabımı yönet</ActionLink></div>}
      {profile && <>
        <div className="account-grid"><div className="account-column">
        <AccountForm<{user: User}> requireChanges title="Profil bilgileri" path="profile" method="PATCH" fields={fields} submit="Profili kaydet" onSuccess={data => setUser(data.user)}>
          <p>En az 13 yaşında olmalısınız. Kullanıcı adı 3–30 harf, rakam veya alt çizgi içermelidir. Telefon + ile başlayan 8–15 rakam olmalıdır; kaydedilmesi doğrulama sağlamaz.</p>
        </AccountForm>
        </div><div className="account-column"><AccountForm title="E-posta değiştir" path="email/change" fields={[{name: 'email', label: 'Yeni e-posta', type: 'email', maxLength: 254}]} submit="Yeni adrese doğrulama gönder">
          <p>Yeni adres doğrulanana kadar mevcut adresiniz geçerlidir. Eski adresinize bildirim gönderilir. Onaydan sonra bütün oturumlar kapanır.</p>
        </AccountForm>
        <AccountForm title="Şifre değiştir" path="password/change" fields={[{name: 'old_password', label: 'Eski şifre', type: 'password'}, {name: 'password', label: 'Yeni şifre', type: 'password', password: true}]} submit="Şifreyi değiştir" onSuccess={signedOut}>
          <p>Başarıyla değiştirildiğinde bütün oturumlar kapanır; yeni şifrenizle giriş yapın.</p>
        </AccountForm>
        </div></div><SessionList onSignedOut={signedOut}/>
      </>}
      <div className="account-exit"><Button variant="quiet" loading={busy} disabled={busy} onClick={async () => {
        if (lock.current) return;
        lock.current = true; setBusy(true); setError('');
        try {await api('logout', {}); signedOut();}
        catch (caught) {setError((caught as Error).message);}
        finally {lock.current = false; setBusy(false);}
      }}>{busy ? 'Çıkış yapılıyor…' : 'Çıkış yap'}</Button></div>
    </>}
  </div>;
}
