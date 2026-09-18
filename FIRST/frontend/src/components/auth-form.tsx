'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useId, useRef, useState } from 'react';
import { api, ApiError, User } from '../lib/api';
import { passwordHelp } from './account-form';
import { Alert, Button, Checkbox, Field, Input, PageHeading, Select, Surface } from './ui';

export function AuthForm({ register = false }: { register?: boolean }) {
  const router = useRouter();
  const id = useId();
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const field = (name: string, label: string, type = 'text', extra: React.InputHTMLAttributes<HTMLInputElement> = {}, help?: string) => {
    const inputId = `${id}-${name}`;
    const errors = error?.errors[name];
    return <Field key={name} id={inputId} label={label} help={help} error={errors?.join(' ')}>
      <Input id={inputId} name={name} type={type} required={name !== 'phone'} aria-invalid={!!errors} {...extra}
        aria-describedby={[extra['aria-describedby'], help ? `${inputId}-help` : '', errors ? `${inputId}-error` : ''].filter(Boolean).join(' ') || undefined} />
    </Field>;
  };
  const genderId = `${id}-gender`;
  return <Surface className={`form-page${register ? ' register-page' : ''}`}>
    <PageHeading title={register ? 'Hesap oluştur' : 'Giriş yap'}
      description={register ? 'FIRST hesabınız için bilgilerinizi doldurun.' : 'FIRST hesabınıza yeniden hoş geldiniz.'} />
    <form aria-busy={busy} onSubmit={async event => {
      event.preventDefault();
      if (lock.current) return;
      lock.current = true; setBusy(true); setError(null);
      const data = new FormData(event.currentTarget);
      const payload: Record<string, unknown> = Object.fromEntries(data.entries());
      if (register && typeof payload.username === 'string') payload.username = payload.username.normalize('NFC');
      if (!register) payload.remember_me = data.get('remember_me') === 'on';
      try {
        await api<{ user: User }>(register ? 'register' : 'login', payload);
        router.replace('/'); router.refresh();
      } catch (caught) { setError(caught as ApiError); }
      finally { lock.current = false; setBusy(false); }
    }}>
      {error && <Alert role="alert" tone="error"><p>{error.message}</p>{error.errors.non_field_errors?.map(text => <p key={text}>{text}</p>)}</Alert>}
      <fieldset disabled={busy}>
        {field('email', 'E-posta', 'email', { autoComplete: 'email', maxLength: 254 })}
        {register && field('username', 'Kullanıcı adı', 'text', { autoComplete: 'username' })}
        {register && field('full_name', 'Ad soyad', 'text', { autoComplete: 'name', maxLength: 150 })}
        {register && field('birth_date', 'Doğum tarihi', 'date')}
        {register && <>
          <p className="form-hint">En az 13 yaşında olmalısınız. Kullanıcı adı 3–30 harf, rakam veya alt çizgi içermelidir.</p>
          <Field id={genderId} label="Cinsiyet" error={error?.errors.gender?.join(' ')}>
            <Select id={genderId} name="gender" defaultValue="" required aria-invalid={!!error?.errors.gender} aria-describedby={error?.errors.gender ? `${genderId}-error` : undefined}>
              <option value="" disabled>Seçiniz</option><option value="female">Kadın</option><option value="male">Erkek</option><option value="other">Diğer</option><option value="unspecified">Belirtmek istemiyorum</option>
            </Select>
          </Field>
        </>}
        {register && field('phone', 'Telefon (isteğe bağlı, doğrulanmaz)', 'tel', { autoComplete: 'tel', maxLength: 32, placeholder: '+905551234567' })}
        {field('password', 'Şifre', 'password', { autoComplete: register ? 'new-password' : 'current-password' }, register ? passwordHelp : undefined)}
        {!register && <Checkbox name="remember_me">Beni hatırla (30 gün)</Checkbox>}
        <Button type="submit" loading={busy} className="button--full">{busy ? 'İşlem sürüyor…' : register ? 'Kayıt ol' : 'Giriş yap'}</Button>
      </fieldset>
    </form>
    <div className="form-links"><Link href={register ? '/giris' : '/kayit'}>{register ? 'Zaten hesabım var' : 'Hesap oluştur'}</Link>
      {!register && <Link href="/sifremi-unuttum">Şifremi unuttum</Link>}
    </div>
  </Surface>;
}
