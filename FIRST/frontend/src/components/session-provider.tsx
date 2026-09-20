'use client';
import {createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode} from 'react';
import {usePathname} from 'next/navigation';
import {api, sessionChangedEvent, sessionKey, type SessionChange, type User} from '../lib/api';
import {ActionLink, Alert, Button, PageHeading, Surface} from './ui';

type SessionState = {status: 'loading' | 'ready' | 'error'; user: User | null; error: string};
type SessionContextValue = SessionState & {refresh: () => Promise<void>; updateUser: (user: User | null) => void};
const SessionContext = createContext<SessionContextValue | null>(null);
export function SessionProvider({children}: {children: ReactNode}) {
  const [state, setState] = useState<SessionState>({status: 'loading', user: null, error: ''});
  const revision = useRef(0);
  const refresh = useCallback(async (background = false) => {
    const current = ++revision.current;
    if(!background) setState({status: 'loading', user: null, error: ''});
    try {
      const result = await api<{user: User | null}>('me');
      if(current === revision.current) setState({status: 'ready', user: result.user, error: ''});
    } catch(error) {
      if(current === revision.current) setState(previous => background && previous.status === 'ready' ? {...previous, error: (error as Error).message} : {status: 'error', user: null, error: (error as Error).message});
    }
  }, []);
  const updateUser = useCallback((user: User | null) => {
    revision.current++;
    setState({status: 'ready', user, error: ''});
  }, []);
  useEffect(() => {
    const changed = (event: Event) => {
      const detail = (event as CustomEvent<SessionChange>).detail;
      if(detail && Object.hasOwn(detail, 'user')) updateUser(detail.user ?? null);
      else void refresh(detail?.revalidate === true);
    };
    const storage = (event: StorageEvent) => {
      if(event.storageArea === localStorage && (event.key === sessionKey || event.key === null)) void refresh();
    };
    // Returning from an email verification or another device's session revocation
    // should also refresh the identity, without assuming an outage means logout.
    const visible = () => {if(document.visibilityState === 'visible') void refresh(true);};
    window.addEventListener(sessionChangedEvent, changed);
    window.addEventListener('storage', storage);
    document.addEventListener('visibilitychange', visible);
    void refresh();
    return () => {revision.current++; window.removeEventListener(sessionChangedEvent, changed); window.removeEventListener('storage', storage); document.removeEventListener('visibilitychange', visible);};
  }, [refresh, updateUser]);
  return <SessionContext.Provider value={{...state, refresh, updateUser}}>{children}</SessionContext.Provider>;
}
export function useSession() {
  const context = useContext(SessionContext);
  if(!context) throw new Error('SessionProvider is required');
  return context;
}
export function SessionPending() {
  const {status, error, refresh} = useSession();
  return status === 'error' ? <Alert tone="error" role="alert"><p>{error}</p><Button variant="secondary" onClick={() => void refresh()}>Yeniden dene</Button></Alert> : <Alert role="status">Hesap bilgileri yükleniyor…</Alert>;
}
export function RequireSession({children}: {children: ReactNode}) {
  const {status, user} = useSession();
  if(status !== 'ready') return <SessionPending/>;
  if(!user) return <Surface className="form-page"><PageHeading title="Devam etmek için giriş yapın" description="Bu alan, hesabınıza ait bilgileri ve paylaşımları içerir."/><div className="action-row"><ActionLink href="/giris">Giriş yap</ActionLink><ActionLink href="/kayit" variant="secondary">Hesap oluştur</ActionLink></div></Surface>;
  return <div key={user.id}>{children}</div>;
}
export function GuestOnly({children}: {children: ReactNode}) {
  const {status, user} = useSession();
  if(status !== 'ready') return <SessionPending/>;
  if(user) return <Surface className="form-page"><PageHeading title="Zaten giriş yaptınız" description={`${user.full_name || user.username}, hesabınızla devam edebilirsiniz.`}/><div className="action-row"><ActionLink href="/">Ana sayfaya git</ActionLink><ActionLink href="/hesap" variant="secondary">Hesabım</ActionLink></div></Surface>;
  return children;
}
export function SessionNavigation() {
  const {status, user, refresh, error: sessionError} = useSession();
  const pathname = usePathname();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const lock = useRef(false);
  const current = (href: string) => pathname === href || (href !== '/' && pathname.startsWith(`${href}/`));
  return <div className="navigation-group"><nav className="site-nav" aria-label="Ana gezinme">
    {status === 'loading' ? <span className="nav-status" role="status">Hesap yükleniyor…</span> : status === 'error' ? <Button variant="quiet" onClick={() => void refresh()}>Hesabı yeniden kontrol et</Button> : user ? <>
      {[['/', 'Projeleri keşfet'], ['/projelerim', 'Projelerim'], ['/basvurular', 'Başvurular'], ['/bildirimler', 'Bildirimler'], ['/hesap', 'Hesabım']].map(([href, label]) => <ActionLink key={href} href={href} variant="quiet" aria-current={current(href) ? 'page' : undefined}>{label}</ActionLink>)}
      <Button variant="quiet" loading={busy} onClick={async () => {
        if(lock.current) return; lock.current = true; setBusy(true); setError('');
        try {await api('logout', {});} catch(caught) {setError((caught as Error).message);} finally {lock.current = false; setBusy(false);}
      }}>{busy ? 'Çıkış yapılıyor…' : 'Çıkış yap'}</Button>
    </> : <><ActionLink href="/" variant="quiet" aria-current={current('/') ? 'page' : undefined}>Projeleri keşfet</ActionLink><ActionLink href="/giris" variant="quiet" aria-current={current('/giris') ? 'page' : undefined}>Giriş yap</ActionLink><ActionLink href="/kayit" aria-current={current('/kayit') ? 'page' : undefined}>Hesap oluştur</ActionLink></>}
  </nav>{sessionError && status === 'ready' && <Alert role="alert" tone="error"><p>{sessionError}</p><Button variant="secondary" onClick={() => void refresh()}>Hesabı yeniden kontrol et</Button></Alert>}{error && <Alert role="alert" tone="error">{error}</Alert>}</div>;
}
