'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, User } from '../lib/api';
export function AccountStatus(){
 const router=useRouter();const lock=useRef(false);const [user,setUser]=useState<User|null|undefined>(undefined);const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 useEffect(()=>{let active=true;api<{user:User|null}>('me').then(data=>{if(active)setUser(data.user);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[]);
 return <section className="card"><h1>Hesabım</h1>{error&&<p role="alert">{error}</p>}{user===undefined&&!error&&<p role="status">Oturum kontrol ediliyor…</p>}{user===null&&<p>Oturumunuz açık değil. <Link href="/giris">Giriş yapın</Link>.</p>}{user&&<><p>Merhaba, {user.full_name}.</p>{!user.email_verified&&<p>E-posta adresiniz henüz doğrulanmadı.</p>}<p>Giriş ve kayıt hazır. Ana sayfa ve profil yönetimi sonraki uygulama aşamasında eklenecek.</p><button disabled={busy} onClick={async()=>{if(lock.current)return;lock.current=true;setBusy(true);setError('');try{await api('logout',{});setUser(null);router.replace('/giris');router.refresh();}catch(e){setError((e as Error).message);}finally{lock.current=false;setBusy(false);}}}>{busy?'Çıkış yapılıyor…':'Çıkış yap'}</button></>}</section>;
}
