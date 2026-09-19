 'use client';
import Link from 'next/link';
import {useEffect, useState} from 'react';
import {useRouter} from 'next/navigation';
import {ApiError, oauthCallback, oauthDestination} from '../lib/api';
import {Alert, PageHeading, Surface} from './ui';

// The same promise survives StrictMode's effect replay without consuming OAuth state twice.
const callbacks = new Map<string, Promise<string>>();
export function OAuthCallback({provider}:{provider:'google'|'github'|'github_app'}) {
  const router = useRouter();
  const [error,setError] = useState('');
  const [search] = useState(()=>typeof window === 'undefined' ? '' : window.location.search);
  useEffect(()=>{
    let active = true;
    let work = callbacks.get(provider + search);
    if(!work) {
      const query = new URLSearchParams(search);
      window.history.replaceState(null,'',window.location.pathname);
      work = (async()=>{
        const forwarded = new URLSearchParams();
        for(const key of ['code','state','error']) {
          const values = query.getAll(key);
          if(values.length > 1 || (values[0]?.length || 0) > 4096) throw new ApiError('Geçersiz sağlayıcı dönüşü.',400);
          if(values.length) forwarded.set(key,values[0]);
        }
        const path = provider === 'github_app' ? 'projects/github/callback' : `${provider}/callback`;
        try {return oauthDestination((await oauthCallback(path,forwarded)).redirect_to);}
        catch(caught) {
          if(caught instanceof ApiError && caught.redirectTo) return oauthDestination(caught.redirectTo);
          throw caught;
        }
      })();
      if(callbacks.size >= 8) callbacks.delete(callbacks.keys().next().value!);
      callbacks.set(provider + search,work);
    }
    work.then(destination=>{if(active){router.replace(destination);router.refresh();}})
      .catch(caught=>{if(active)setError(caught instanceof Error ? caught.message : 'Giriş tamamlanamadı.');});
    return ()=>{active = false;};
  },[provider,router,search]);
  return <Surface className="form-page"><PageHeading title="Hesabınıza bağlanılıyor"/>
    {error ? <Alert role="alert" tone="error">{error} <Link href="/giris">Girişe dön</Link></Alert> : <Alert role="status">Lütfen bekleyin…</Alert>}
  </Surface>;
}
