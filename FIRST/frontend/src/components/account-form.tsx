'use client';
import Link from 'next/link';
import { useId, useRef, useState } from 'react';
import { api, ApiError } from '../lib/api';

export type Field = {
  name: string; label: string; type?: string; value?: string;
  optional?: boolean; password?: boolean; maxLength?: number;
  options?: [string, string][];
};
export const passwordHelp = '8–20 karakter; boşluk içermemeli. Büyük harf, küçük harf, sayı ve özel karakter zorunludur. Türkçe karakter kullanabilirsiniz.';

/** Every mutation obtains fresh CSRF; a reauth challenge never silently retries it. */
export function AccountForm<T = {detail: string}>({title, path, method = 'POST', fields = [], extra = {}, submit, children, onSuccess}: {
  title: string; path: string; method?: string; fields?: Field[];
  extra?: Record<string, string>; submit: string; children?: React.ReactNode;
  onSuccess?: (result: T) => void | Promise<void>;
}) {
  const id = useId();
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [message, setMessage] = useState('');
  const [reauth, setReauth] = useState(false);
  return <section className="account-section" aria-labelledby={`${id}-title`}>
    <h2 id={`${id}-title`}>{title}</h2>
    {children}
    <form aria-label={title} aria-busy={busy} onSubmit={async event => {
      event.preventDefault();
      if (lock.current) return;
      lock.current = true; setBusy(true); setError(null); setMessage('');
      const payload = Object.fromEntries(new FormData(event.currentTarget));
      if (typeof payload.username === 'string') payload.username = payload.username.normalize('NFC');
      try {
        const result = await api<T>(path, {...payload, ...extra}, method);
        setMessage((result as {detail?: string}).detail || 'Bilgiler güncellendi.');
        await onSuccess?.(result);
      } catch (caught) {
        const failure = caught as ApiError;
        setError(failure);
        if (failure.code === 'reauthentication_required') setReauth(true);
      } finally { lock.current = false; setBusy(false); }
    }}>
      {error && <div role="alert" className="error"><p>{error.message}</p>
        {error.errors.non_field_errors?.map(value => <p key={value}>{value}</p>)}
        {error.status === 401 && <Link href="/giris">Oturumunuz sona erdi. Yeniden giriş yapın.</Link>}
      </div>}
      {message && <p role="status">{message}</p>}
      <fieldset disabled={busy || reauth}>
        {fields.map(field => {
          const inputId = `${id}-${field.name}`;
          const errors = error?.errors[field.name];
          const common = {id: inputId, name: field.name, required: !field.optional,
            defaultValue: field.value, 'aria-invalid': !!errors,
            'aria-describedby': [errors ? `${inputId}-error` : '', field.password ? `${inputId}-help` : ''].filter(Boolean).join(' ') || undefined};
          return <div className="field" key={field.name}>
            <label htmlFor={inputId}>{field.label}</label>
            {field.options ? <select {...common}>{field.options.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select>
              : <input {...common} type={field.type || 'text'} maxLength={field.maxLength}
                autoComplete={field.type === 'password' ? (field.password ? 'new-password' : 'current-password') : undefined}/>}
            {field.password && <p id={`${inputId}-help`}>{passwordHelp}</p>}
            {errors && <p className="error" id={`${inputId}-error`}>{errors.join(' ')}</p>}
          </div>;
        })}
        <button type="submit">{busy ? 'İşlem sürüyor…' : submit}</button>
      </fieldset>
    </form>
    {reauth && <AccountForm title="Kimliğinizi yeniden doğrulayın" path="reauthenticate"
      fields={[{name: 'password', label: 'Mevcut şifreniz', type: 'password'}]} submit="Kimliğimi doğrula"
      onSuccess={() => {setReauth(false); setError(null); setMessage('Kimliğiniz doğrulandı. İşleminizi yeniden gönderin.');}}/>}
  </section>;
}
