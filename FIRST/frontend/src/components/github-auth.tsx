'use client';
import { useContext, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../lib/api';
import { AccountForm, ReauthenticationContext, ReauthenticationOptions } from './account-form';
import { Alert, Button } from './ui';

export function GitHubButton({remember = false, purpose = 'login', disabled = false, onBusyChange}: {remember?: boolean; purpose?: 'login' | 'link'; disabled?: boolean; onBusyChange?: (busy: boolean) => void}) {
  const methods = useContext(ReauthenticationContext);
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [reauth, setReauth] = useState(false);
  const lock = useRef(false);
  useEffect(() => {
    let active = true;
    api<{providers: {github: boolean}}>('config').then(data => {if(active) setEnabled(data.providers?.github === true);}).catch(() => {});
    return () => {active = false;};
  }, []);
  if (!enabled) return null;
  return <div className="google-auth">
    {error && <Alert role="alert" tone="error">{error}</Alert>}
    <Button variant="secondary" className="button--full" loading={busy} disabled={disabled || reauth} onClick={async () => {
      if(lock.current) return;
      lock.current = true; setBusy(true); onBusyChange?.(true); setError('');
      try {
        const result = await api<{authorization_url: string}>('github/start', {remember_me: remember, purpose});
        const target = new URL(result.authorization_url);
        if(target.origin !== 'https://github.com' || target.pathname !== '/login/oauth/authorize' || target.username || target.password) throw new Error('GitHub giriş adresi doğrulanamadı.');
        window.location.assign(target.href);
      } catch(caught) {
        setError((caught as Error).message);
        if(purpose === 'link' && caught instanceof ApiError && caught.code === 'reauthentication_required') setReauth(true);
        lock.current = false; setBusy(false); onBusyChange?.(false);
      }
    }}>{busy ? 'GitHub’a yönlendiriliyor…' : purpose === 'link' ? 'GitHub hesabımı bağla' : 'GitHub ile devam et'}</Button>
    <p className="field-help">İlk bağlantıda, seçtiğiniz repolara erişim iznini de GitHub’da tamamlarsınız.</p>
    {reauth && <>
      <ReauthenticationOptions methods={methods}/>
      {methods.password && <AccountForm title="Kimliğinizi yeniden doğrulayın" path="reauthenticate" fields={[{name: 'password', label: 'Mevcut şifreniz', type: 'password'}]} submit="Kimliğimi doğrula" onSuccess={() => {setReauth(false); setError('');}}/>}
    </>}
  </div>;
}
