'use client';
import Link from 'next/link';
import { useEffect, useId, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '../lib/api';
import { Alert, Button, Field, Input, PageHeading, Select, Surface } from './ui';

type Pending = {profile: {email: string; full_name: string; username: string; birth_date: string; gender: string; phone: string}; email_verified: boolean; email_editable: boolean};
export function SocialSignup({provider}: {provider: 'google' | 'github'}) {
  const label = provider === 'google' ? 'Google' : 'GitHub';
  const router = useRouter();
  const id = useId();
  const lock = useRef(false);
  const [pending, setPending] = useState<Pending | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => {let active = true;
    api<Pending>(`${provider}/signup`).then(data => {if(active) setPending(data);}).catch(caught => {if(active) setError(caught);});
    return () => {active = false;};
  }, [provider]);
  const fields = [['email', 'E-posta', 'email'], ['full_name', 'Ad soyad', 'text'], ['username', 'Kullanıcı adı', 'text'], ['birth_date', 'Doğum tarihi', 'date'], ['phone', 'Telefon (isteğe bağlı, doğrulanmaz)', 'tel']] as const;
  return <Surface className="form-page register-page"><PageHeading title="Kaydınızı tamamlayın" description={`${label} hesabınızdan gelen bilgileri kontrol edin ve eksik alanları doldurun. Şifre oluşturmanız gerekmiyor.}`}/>
    {error && <Alert role="alert" tone="error"><p>{error.message}</p>{error.errors.non_field_errors?.map(text => <p key={text}>{text}</p>)}{(!pending || error.code === `${provider}_signup_expired`) && <Link href="/giris">{label} ile yeniden giriş yap</Link>}</Alert>}
    {!pending && !error && <Alert role="status">{label} bilgileri yükleniyor…</Alert>}
    {message && <Alert role="status" tone="success">{message}</Alert>}
    {pending && <form aria-busy={busy} onSubmit={async event => {
      event.preventDefault(); if(lock.current || !pending.email_verified) return;
      lock.current = true; setBusy(true); setError(null);
      const payload = Object.fromEntries(new FormData(event.currentTarget));
      if(typeof payload.username === 'string') payload.username = payload.username.normalize('NFC');
      if(!pending.email_editable) delete payload.email;
      try {await api(`${provider}/signup`, payload); router.replace('/'); router.refresh();}
      catch(caught) {setError(caught as ApiError);}
      finally {lock.current = false; setBusy(false);}
    }}><fieldset disabled={busy}>
      {fields.map(([name, label, type]) => <Field key={name} id={`${id}-${name}`} label={label} error={error?.errors[name]?.join(' ')}>
        <Input id={`${id}-${name}`} name={name} type={type} defaultValue={pending.profile[name] || ''} required={name !== 'phone'} readOnly={name === 'email' && !pending.email_editable}
          autoComplete={name === 'full_name' ? 'name' : name === 'phone' ? 'tel' : name === 'email' ? 'email' : name === 'username' ? 'username' : 'bday'}
          maxLength={name === 'email' ? 254 : name === 'full_name' ? 150 : name === 'phone' ? 32 : undefined}
          aria-invalid={!!error?.errors[name]} aria-describedby={error?.errors[name] ? `${id}-${name}-error` : undefined}/>
      </Field>)}
      {!pending.email_verified && <div><p className="form-hint">Kaydınızı tamamlamadan önce e-posta adresinizi doğrulayın. Bağlantıyı bu tarayıcıda açın; mevcut bir hesabınız varsa doğrulama sonrası o hesaba giriş yapılır.</p>
        <Button variant="secondary" disabled={busy} onClick={async event => {
          const form = event.currentTarget.form;
          const input = form?.elements.namedItem('email') as HTMLInputElement | null;
          if(!input?.reportValidity() || lock.current) return;
          lock.current = true; setBusy(true); setError(null); setMessage('');
          try {const result = await api<{detail: string}>(`${provider}/email/request`, {email: input.value}); setMessage(result.detail);}
          catch(caught) {setError(caught as ApiError);}
          finally {lock.current = false; setBusy(false);}
        }}>E-posta doğrulama bağlantısı gönder</Button>
      </div>}
      <Field id={`${id}-gender`} label="Cinsiyet" error={error?.errors.gender?.join(' ')}>
        <Select id={`${id}-gender`} name="gender" defaultValue={pending.profile.gender || ''} required aria-invalid={!!error?.errors.gender} aria-describedby={error?.errors.gender ? `${id}-gender-error` : undefined}>
          <option value="" disabled>Seçiniz</option><option value="female">Kadın</option><option value="male">Erkek</option><option value="other">Diğer</option><option value="unspecified">Belirtmek istemiyorum</option>
        </Select>
      </Field>
      <p className="form-hint">En az 13 yaşında olmalısınız. Kullanıcı adı 3–30 harf, rakam veya alt çizgi içermelidir.</p>
      <Button type="submit" loading={busy} disabled={!pending.email_verified} className="button--full">{busy ? 'Kaydınız tamamlanıyor…' : 'Kaydı tamamla'}</Button>
    </fieldset></form>}
    <div className="form-links"><Link href="/giris">Girişe dön</Link></div>
  </Surface>;
}
