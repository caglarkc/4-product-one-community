'use client';
import Link from 'next/link';
import { useContext, useId, useRef, useState } from 'react';
import { api, ApiError, type User } from '../lib/api';
import { AccountForm, ReauthenticationContext, ReauthenticationOptions } from './account-form';
import { Alert, Button, Field, Input, Surface } from './ui';

export type ResetResult = {detail: string; user?: User; github_cleanup_required?: boolean};
type Action = 'github' | 'repositories' | 'account';
const actions = {
  github: {title: 'GitHub hesap bağlantısını kaldır', path: 'github/disconnect', confirmation: 'GITHUB', submit: 'GitHub bağlantısını kaldırmayı onayla'},
  repositories: {title: 'GitHub repo izinlerini kaldır', path: 'projects/github/disconnect', confirmation: 'REPO', submit: 'Repo izinlerini kaldırmayı onayla'},
  account: {title: 'FIRST hesabımı sil', path: 'account', confirmation: 'HESABIMI SIL', submit: 'Hesabımı kalıcı olarak sil'},
};

function ConfirmedAction({action, activeAction, setActiveAction, onChanged, onDeleted}: {action: Action; activeAction: Action | null; setActiveAction: (action: Action | null) => void; onChanged: (result: ResetResult) => void; onDeleted: (result: ResetResult) => void}) {
  const config = actions[action];
  const id = useId();
  const methods = useContext(ReauthenticationContext);
  const lock = useRef(false);
  const open = activeAction === action;
  const setOpen = (value: boolean) => setActiveAction(value ? action : null);
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
    const [reauth, setReauth] = useState(false);
  const deleting = action === 'account';
  return <div className="account-reset-action">
    <h3>{config.title}</h3>
    <p>{action === 'github' ? 'GitHub ile FIRST girişi ve repo erişimi kaldırılır. Paylaşımlarınız arşivlenir. Başka bir giriş yönteminizin bulunması gerekir.' : action === 'repositories' ? 'Repo erişim yetkisi iptal edilir ve paylaşımlarınız arşivlenir. GitHub ile FIRST girişiniz devam eder.' : 'FIRST profiliniz, paylaşımlarınız ve oturumlarınız kalıcı olarak silinir. Bu işlem geri alınamaz.'}</p>
    {!open ? <Button variant="danger" disabled={activeAction !== null} onClick={() => {setOpen(true); setError(null);}} aria-expanded={false}>{config.title}</Button> : <>
      <form aria-label={`${config.title} onayı`} aria-busy={busy} onSubmit={async event => {
        event.preventDefault();
        if (lock.current || reauth || (deleting && confirmation !== config.confirmation)) return;
        lock.current = true; setBusy(true); setError(null);
        try {
          const result = await api<ResetResult>(config.path, {confirmation: config.confirmation}, deleting ? 'DELETE' : 'POST');
          if (deleting) {onDeleted(result); return;}
          onChanged(result); setOpen(false); setConfirmation('');
        } catch (caught) {
          const failure = caught as ApiError;
          setError(failure);
          if (failure.code === 'reauthentication_required') setReauth(true);
        } finally {lock.current = false; setBusy(false);}
      }}>
        <Alert><p>GitHub’a ulaşılamazsa FIRST bağlantısı yine kaldırılır; GitHub ayarlarından kalan izni kaldırmanız gerekir.</p><p>{deleting ? 'GitHub hesabınız ve GitHub repolarınız silinmez.' : 'Diğer FIRST oturumlarınız kapatılır; bu oturum açık kalır. GitHub repolarınız silinmez.'}</p></Alert>
        {error && <Alert tone="error" role="alert"><p>{error.message}</p>
          {error.status === 401 && <Link href="/giris">Yeniden giriş yapın</Link>}
          {error.code === 'last_login_method' && <Link href="/sifremi-unuttum">E-posta bağlantısıyla şifre oluşturun</Link>}
        </Alert>}
        <fieldset disabled={busy || reauth}>
          {deleting && <Field id={`${id}-confirmation`} label="Onaylamak için HESABIMI SIL yazın">
            <Input id={`${id}-confirmation`} value={confirmation} onChange={event => setConfirmation(event.target.value)} autoComplete="off" required/>
          </Field>}
          <Button type="submit" variant="danger" loading={busy} disabled={deleting && confirmation !== config.confirmation}>{busy ? 'İşlem sürüyor…' : config.submit}</Button>
        </fieldset>
      </form>
      {reauth && <ReauthenticationOptions methods={methods}/>}
      {reauth && methods.password && <AccountForm title="Kimliğinizi yeniden doğrulayın" path="reauthenticate" fields={[{name: 'password', label: 'Mevcut şifreniz', type: 'password'}]} submit="Kimliğimi doğrula" onSuccess={() => {setReauth(false); setError(null);}}/>}
      <Button variant="quiet" disabled={busy} onClick={() => {setOpen(false); setConfirmation(''); setError(null); setReauth(false);}}>Vazgeç</Button>
    </>}
  </div>;
}

export function AccountReset({user, onChanged, onDeleted}: {user: User; onChanged: (user: User) => void; onDeleted: (result: ResetResult) => void}) {
  const github = user.providers?.includes('github');
  const [activeAction, setActiveAction] = useState<Action | null>(null);
  const [result, setResult] = useState<ResetResult | null>(null);
  function changed(updated: ResetResult) {setActiveAction(null); setResult(updated); if (updated.user) onChanged(updated.user);}
  return <Surface className="account-section account-reset"><h2>Bağlantıları kaldırma ve hesap silme</h2>
    {result && <Alert tone={result.github_cleanup_required ? 'info' : 'success'} role="status">{result.detail}{result.github_cleanup_required && <p><a href="https://github.com/settings/applications" target="_blank" rel="noopener noreferrer">GitHub’da kalan izni kaldırın (yeni sekme)</a></p>}</Alert>}
    <p>Bu işlemler erişimlerinizi veya hesabınızı kaldırır. Devam etmeden önce her işlemin etkisini gözden geçirin. GitHub hesabınız ve repolarınız silinmez.</p>
    {github && <>
      <ConfirmedAction action="github" activeAction={activeAction} setActiveAction={setActiveAction} onChanged={changed} onDeleted={onDeleted}/>
      <ConfirmedAction action="repositories" activeAction={activeAction} setActiveAction={setActiveAction} onChanged={changed} onDeleted={onDeleted}/>
    </>}
    <ConfirmedAction action="account" activeAction={activeAction} setActiveAction={setActiveAction} onChanged={changed} onDeleted={onDeleted}/>
    <p>GitHub giriş uygulamasına verdiğiniz onayı da kaldırmak için <a href="https://github.com/settings/applications" target="_blank" rel="noopener noreferrer">GitHub yetkili uygulamalarını</a>; kurulumu kaldırmak için <a href="https://github.com/settings/installations" target="_blank" rel="noopener noreferrer">GitHub App kurulumlarını</a> yönetin (yeni sekme).</p>
  </Surface>;
}
