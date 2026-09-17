'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { api, ApiError, User } from '../lib/api';

export function AuthForm({register=false}:{register?:boolean}){
  const router=useRouter();const lock=useRef(false);
  const [busy,setBusy]=useState(false);const [error,setError]=useState<ApiError|null>(null);
  const field=(name:string,label:string,type='text',extra:React.InputHTMLAttributes<HTMLInputElement>={})=><div className="field" key={name}>
    <label htmlFor={name}>{label}</label><input id={name} name={name} type={type} required={name!=='phone'} aria-invalid={!!error?.errors[name]} {...extra} aria-describedby={[extra["aria-describedby"],error?.errors[name]?`${name}-error`:null].filter(Boolean).join(" ") || undefined}/>
    {error?.errors[name]&&<p id={`${name}-error`} className="error">{error.errors[name].join(' ')}</p>}
  </div>;
  return <section className="card"><h1>{register?'Hesap oluştur':'Giriş yap'}</h1>
    <form aria-busy={busy} onSubmit={async event=>{
      event.preventDefault();if(lock.current)return;lock.current=true;setBusy(true);setError(null);
      const data=new FormData(event.currentTarget);
      const payload:Record<string,unknown>=Object.fromEntries(data.entries());
      if(register && typeof payload.username==='string')payload.username=payload.username.normalize('NFC');
      if(!register)payload.remember_me=data.get('remember_me')==='on';
      try{await api<{user:User}>(register?'register':'login',payload);router.replace('/hesap');router.refresh();}
      catch(e){setError(e as ApiError);}finally{lock.current=false;setBusy(false);}
    }}>
      {error&&<div role="alert" className="error"><p>{error.message}</p>{error.errors.non_field_errors?.map(text=><p key={text}>{text}</p>)}</div>}
      <fieldset disabled={busy}>
        {field('email','E-posta','email',{autoComplete:'email',maxLength:254})}
        {register&&field('username','Kullanıcı adı','text',{autoComplete:'username'})}
        {register&&field('full_name','Ad soyad','text',{autoComplete:'name',maxLength:150})}
        {register&&field('birth_date','Doğum tarihi','date')}
        {register&&<><p>En az 13 yaşında olmalısınız. Kullanıcı adı 3–30 harf, rakam veya alt çizgi içermelidir.</p><div className="field"><label htmlFor="gender">Cinsiyet</label><select id="gender" name="gender" defaultValue="" required aria-invalid={!!error?.errors.gender} aria-describedby={error?.errors.gender?'gender-error':undefined}><option value="" disabled>Seçiniz</option><option value="female">Kadın</option><option value="male">Erkek</option><option value="other">Diğer</option><option value="unspecified">Belirtmek istemiyorum</option></select>{error?.errors.gender&&<p className="error" id="gender-error">{error.errors.gender.join(' ')}</p>}</div></>}
        {register&&field('phone','Telefon (isteğe bağlı, doğrulanmaz)','tel',{autoComplete:'tel',maxLength:32,placeholder:'+905551234567'})}
        {field('password','Şifre','password',{autoComplete:register?'new-password':'current-password',...(register?{minLength:8,maxLength:20,'aria-describedby':'password-help'}:{})})}
        {register&&<p id="password-help">8–20 karakter; boşluk içermemeli. Büyük harf, küçük harf, sayı ve özel karakter zorunludur. Türkçe karakter kullanabilirsiniz.</p>}
        {!register&&<label className="check"><input name="remember_me" type="checkbox"/> Beni hatırla (30 gün)</label>}
        <button type="submit">{busy?'İşlem sürüyor…':register?'Kayıt ol':'Giriş yap'}</button>
      </fieldset>
    </form><p><Link href={register?'/giris':'/kayit'}>{register?'Zaten hesabım var':'Hesap oluştur'}</Link></p>
  </section>;
}
