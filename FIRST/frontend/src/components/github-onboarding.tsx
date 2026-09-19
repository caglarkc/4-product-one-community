'use client';
import {useEffect, useRef, useState} from 'react';
import {useRouter} from 'next/navigation';
import {api, User} from '../lib/api';
import {GitHubStatus, Repository} from '../lib/projects';
import {githubNext, navigateToGitHub} from '../lib/github-onboarding';
import {ActionLink, Alert, Button, PageHeading, Surface} from './ui';

const nextKey = 'first.github.setup.next';
const manageKey = 'first.github.setup.manage';
function stored(key: string) {try {return sessionStorage.getItem(key);} catch {return null;}}
function store(key: string, value: string | null) {try {if (value === null) sessionStorage.removeItem(key); else sessionStorage.setItem(key, value);} catch {/* Optional navigation context; authorization never depends on storage. */}}
export function GitHubOnboarding({next, failed = false, installationReturn = false, authorizationReturn = false, manage = false}: {next?: string; failed?: boolean; installationReturn?: boolean; authorizationReturn?: boolean; manage?: boolean}) {
  const router = useRouter();
  const navigating = useRef(false);
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState('');
  const [state, setState] = useState<'loading' | 'login' | 'link' | 'retry' | 'disabled' | 'empty'>('loading');
  const [installation, setInstallation] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    async function setup() {
      try {
        if (attempt === 0 && !manage && !authorizationReturn && !installationReturn && !failed) store(manageKey, null);
        const destination = githubNext(next ?? ((installationReturn || authorizationReturn || failed) ? stored(nextKey) : null));
        const {user} = await api<{user: User | null}>('me');
        if (!active) return;
        if (!user) {setState('login'); return;}
        if (!user.providers.includes('github')) {setState('link'); return;}
        const status = await api<GitHubStatus>('projects/github/status');
        if (!active) return;
        setInstallation(status.installation_url);
        if (!status.enabled) {setState('disabled'); return;}
        if (failed && attempt === 0) {setState('retry'); setError('GitHub repo izni tamamlanamadı veya iptal edildi. FIRST oturumunuz açık; tekrar deneyebilirsiniz.'); return;}
        if (!status.connected) {
          if ((authorizationReturn || installationReturn) && attempt === 0) {setState('retry'); setError('GitHub repo erişimi doğrulanamadı. Bağlantıyı yeniden deneyebilirsiniz.'); return;}
          if (navigating.current) return;
          navigating.current = true;
          store(manageKey, manage || stored(manageKey) === '1' ? '1' : null); store(nextKey, destination);
          const result = await api<{authorization_url: string}>('projects/github/start', {return_to: destination});
          if (!active) return;
          navigateToGitHub(result.authorization_url);
          return;
        }
        const {repositories} = await api<{repositories: Repository[]}>('projects/github/repositories');
        if (!active) return;
        if (repositories.length && (!(manage || stored(manageKey) === '1') || installationReturn)) {
          store(nextKey, null); store(manageKey, null);
          router.replace(destination); router.refresh(); return;
        }
        if (installationReturn || !status.installation_url) {setState('empty'); return;}
        if (navigating.current) return;
        navigating.current = true;
        store(nextKey, destination); store(manageKey, null);
        navigateToGitHub(status.installation_url, true);
      } catch (caught) {
        if (active) {navigating.current = false; setError((caught as Error).message); setState('retry');}
      }
    }
    void setup();
    return () => {active = false;};
  }, [attempt, authorizationReturn, failed, installationReturn, manage, next, router]);
  return <Surface className="form-page"><PageHeading title="GitHub repo izinleri" description="FIRST yalnızca GitHub’da seçtiğiniz repolara erişir. İlk bağlantıda izinleri tamamlayın; sonraki paylaşımlarda reponuzu listeden seçin."/>
    {error && <Alert role="alert" tone="error">{error}</Alert>}
    {state === 'loading' && <Alert role="status">GitHub bağlantınız kontrol ediliyor…</Alert>}
    {state === 'login' && <Alert><p>Devam etmek için GitHub ile giriş yapın.</p><ActionLink href="/giris">Giriş yap</ActionLink></Alert>}
    {state === 'link' && <Alert><p>Önce hesabınıza GitHub hesabınızı bağlayın. Repo izinleri ardından aynı akışta tamamlanır.</p><ActionLink href="/hesap">Hesabıma git</ActionLink></Alert>}
    {state === 'disabled' && <Alert>GitHub repo bağlantısı şu anda kullanılamıyor. Daha sonra tekrar deneyebilirsiniz.</Alert>}
    {state === 'retry' && <Button onClick={() => {navigating.current = false; setError(''); setState('loading'); setAttempt(value => value + 1);}}>İzinleri tamamlamayı yeniden dene</Button>}
    {state === 'empty' && <Alert><p>Henüz erişilebilir repo bulunamadı. GitHub’da yönetici olduğunuz bir repoyu seçip izin verin. Kurulum onayı bekleniyorsa onaylandıktan sonra yeniden kontrol edin.</p>
      {installation && <Button variant="secondary" onClick={() => {try {store(nextKey, githubNext(next ?? stored(nextKey))); navigateToGitHub(installation, true);} catch (caught) {setError((caught as Error).message);}}}>Repo izinlerini yönet</Button>}
      <Button variant="quiet" onClick={() => {setError(''); setState('loading'); setAttempt(value => value + 1);}}>Repo listesini yeniden kontrol et</Button>
    </Alert>}
    <p><ActionLink variant="quiet" href="/hesap">Hesabıma dön</ActionLink></p>
  </Surface>;
}
