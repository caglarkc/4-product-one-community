'use client';
import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';
import { Alert, Button } from './ui';

export function GoogleButton({remember = false, purpose = 'login', disabled = false, onBusyChange}: {remember?: boolean; purpose?: 'login' | 'reauth'; disabled?: boolean; onBusyChange?: (busy: boolean) => void}) {
  const [enabled, setEnabled] = useState(purpose === 'reauth');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const lock = useRef(false);
  useEffect(() => {
    if (purpose === 'reauth') return;
    let active = true;
    api<{providers: {google: boolean}}>('config').then(data => {if(active) setEnabled(data.providers?.google === true);}).catch(() => {});
    return () => {active = false;};
  }, [purpose]);
  if (!enabled) return null;
  return <div className="google-auth">
    {error && <Alert role="alert" tone="error">{error}</Alert>}
    <Button variant="secondary" className="button--full" loading={busy} disabled={disabled} onClick={async () => {
      if(lock.current) return;
      lock.current = true; setBusy(true); onBusyChange?.(true); setError('');
      try {
        const result = await api<{authorization_url: string}>('google/start', {remember_me: remember, purpose});
        const target = new URL(result.authorization_url);
        if(target.origin !== 'https://accounts.google.com' || target.username || target.password) throw new Error('Google giriş adresi doğrulanamadı.');
        window.location.assign(target.href);
      } catch(caught) {setError((caught as Error).message); lock.current = false; setBusy(false); onBusyChange?.(false);}
    }}>{busy ? 'Google’a yönlendiriliyor…' : purpose === 'reauth' ? 'Google ile kimliğimi doğrula' : 'Google ile devam et'}</Button>
  </div>;
}
