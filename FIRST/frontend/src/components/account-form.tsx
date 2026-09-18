'use client';
import Link from 'next/link';
import { createContext, useContext, useId, useRef, useState, type ComponentProps } from 'react';
import { GoogleButton } from './google-auth';
import { api, ApiError } from '../lib/api';
import { Alert, Button, Field as FormField, Input, Select, Surface } from './ui';

export const ReauthenticationContext = createContext({google: false, password: true});

export type Field = {
  name: string; label: string; type?: string; value?: string;
  optional?: boolean; password?: boolean; maxLength?: number;
  options?: [string, string][];
};
export const passwordHelp = '8–20 karakter; boşluk içermemeli. Büyük harf, küçük harf, sayı ve özel karakter zorunludur. Türkçe karakter kullanabilirsiniz.';

/** Every mutation obtains fresh CSRF; a reauth challenge never silently retries it. */
export function AccountForm<T = {detail: string}>({title, path, method = 'POST', fields = [], extra = {}, submit, children, onSuccess, variant = 'primary', requireChanges = false}: {
  requireChanges?: boolean;
  variant?: ComponentProps<typeof Button>['variant'];
  title: string; path: string; method?: string; fields?: Field[];
  extra?: Record<string, string>; submit: string; children?: React.ReactNode;
  onSuccess?: (result: T) => void | Promise<void>;
}) {
  const methods = useContext(ReauthenticationContext);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const normalize = (name: string, value: string) => name === 'username' ? value.normalize('NFC') : value;
  const hasChanges = fields.some(field => normalize(field.name, draft[field.name] ?? field.value ?? '') !== normalize(field.name, field.value ?? ''));
  const id = useId();
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [message, setMessage] = useState('');
  const [reauth, setReauth] = useState(false);
  return <Surface className="account-section" aria-labelledby={`${id}-title`}>
    <h2 id={`${id}-title`}>{title}</h2>
    {children}
    <form aria-label={title} aria-busy={busy} onSubmit={async event => {
      event.preventDefault();
      if (lock.current || reauth || (requireChanges && !hasChanges)) return;
      lock.current = true; setBusy(true); setError(null); setMessage('');
      const payload = Object.fromEntries(new FormData(event.currentTarget));
      if (typeof payload.username === 'string') payload.username = payload.username.normalize('NFC');
      try {
        const result = await api<T>(path, {...payload, ...extra}, method);
        setMessage((result as {detail?: string}).detail || 'Bilgiler güncellendi.');
        await onSuccess?.(result);
        if (requireChanges) setDraft({});
      } catch (caught) {
        const failure = caught as ApiError;
        setError(failure);
        if (failure.code === 'reauthentication_required') setReauth(true);
      } finally { lock.current = false; setBusy(false); }
    }}>
      {error && <Alert role="alert" tone="error"><p>{error.message}</p>
        {error.errors.non_field_errors?.map(value => <p key={value}>{value}</p>)}
        {error.status === 401 && <Link href="/giris">Oturumunuz sona erdi. Yeniden giriş yapın.</Link>}
      </Alert>}
      {message && <Alert role="status" tone="success">{message}</Alert>}
      <fieldset disabled={busy || reauth}>
        {fields.map(field => {
          const inputId = `${id}-${field.name}`;
          const errors = error?.errors[field.name];
          const common = {id: inputId, name: field.name, required: !field.optional,
            ...(requireChanges ? {value: draft[field.name] ?? field.value ?? '', onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setDraft(current => ({...current, [field.name]: event.target.value}))} : {defaultValue: field.value}), 'aria-invalid': !!errors,
            'aria-describedby': [errors ? `${inputId}-error` : '', field.password ? `${inputId}-help` : ''].filter(Boolean).join(' ') || undefined};
          return <FormField key={field.name} id={inputId} label={field.label} help={field.password ? passwordHelp : undefined} error={errors?.join(' ')}>
            {field.options ? <Select {...common}>{field.options.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</Select>
              : <Input {...common} type={field.type || 'text'} maxLength={field.maxLength}
                autoComplete={field.type === 'password' ? (field.password ? 'new-password' : 'current-password') : undefined}/>}
          </FormField>;
        })}
        <Button type="submit" variant={variant} loading={busy} disabled={requireChanges && !hasChanges}>{busy ? 'İşlem sürüyor…' : submit}</Button>
      </fieldset>
    </form>
    {reauth && methods.google && <><p>Google ile kimliğinizi doğruladıktan sonra işleminizi yeniden başlatın.</p><GoogleButton purpose="reauth"/></>}
    {reauth && methods.password && <AccountForm title="Kimliğinizi yeniden doğrulayın" path="reauthenticate"
      fields={[{name: 'password', label: 'Mevcut şifreniz', type: 'password'}]} submit="Kimliğimi doğrula"
      onSuccess={() => {setReauth(false); setError(null); setMessage('Kimliğiniz doğrulandı. İşleminizi yeniden gönderin.');}}/>}
  </Surface>;
}
