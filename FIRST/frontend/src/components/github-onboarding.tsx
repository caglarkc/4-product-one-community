'use client';
import {useEffect, useRef, useState} from 'react';
import {useRouter} from 'next/navigation';
import {api, User} from '../lib/api';
import {GitHubStatus, RepositoryCache, repositoryCacheCaption} from '../lib/projects';
import {githubNext, navigateToGitHub} from '../lib/github-onboarding';
import {ActionLink, Alert, Button, PageHeading, Surface} from './ui';

const nextKey = 'first.github.setup.next';
const manageKey = 'first.github.setup.manage';
function stored(key: string) {try {return sessionStorage.getItem(key);} catch {return null;}}
function store(key: string, value: string | null) {try {if (value === null) sessionStorage.removeItem(key); else sessionStorage.setItem(key, value);} catch {/* Optional navigation context; authorization never depends on storage. */}}
export function GitHubOnboarding({next, failed = false, installationReturn = false, authorizationReturn = false, manage = false}: {next?: string; failed?: boolean; installationReturn?: boolean; authorizationReturn?: boolean; manage?: boolean}) {
  const router = useRouter();
  const navigating = useRef(false);
  const refreshLock = useRef(false);
  const [refreshing, setRefreshing] = useState(false);
  const [authorizing, setAuthorizing] = useState(false);
  const [cache, setCache] = useState<RepositoryCache | null>(null);
  const [destination, setDestination] = useState('/');
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState('');
  const [state, setState] = useState<'loading' | 'login' | 'link' | 'retry' | 'disabled' | 'repositories'>('loading');
  const [installation, setInstallation] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    async function setup() {
      try {
        if (attempt === 0 && !manage && !authorizationReturn && !installationReturn && !failed) store(manageKey, null);
        const destination = githubNext(next ?? ((installationReturn || authorizationReturn || failed) ? stored(nextKey) : null));
        setDestination(destination);
        const {user} = await api<{user: User | null}>('me');
        if (!active) return;
        if (!user) {setState('login'); return;}
        if (!user.providers.includes('github')) {setState('link'); return;}
        const status = await api<GitHubStatus>('projects/github/status');
        if (!active) return;
        setInstallation(status.installation_url);
        if (!status.enabled) {setState('disabled'); return;}
        // Managing an existing connection is explicit: even a local connected
        // flag cannot prove that GitHub still accepts the stored grant.
        if (manage || stored(manageKey) === '1') {
          if(failed) setError('GitHub yetkilendirmesi tamamlanamadı. Bağlantıyı yeniden yetkilendirebilirsiniz.');
          setState('repositories'); return;
        }
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
        const cached = await api<RepositoryCache>('projects/github/repositories');
        if (!active) return;
        setCache(cached);
        // Installation changes do not update the saved list automatically.
        // Always offer an explicit refresh on return, even if the old list is non-empty.
        if (installationReturn) {setState('repositories'); return;}
        if (cached.repositories.length && !(manage || stored(manageKey) === '1')) {
          store(nextKey, null); store(manageKey, null);
          router.replace(destination); router.refresh(); return;
        }
        setState('repositories');
      } catch (caught) {
        if (active) {navigating.current = false; setError((caught as Error).message); setState('retry');}
      }
    }
    void setup();
    return () => {active = false;};
  }, [attempt, authorizationReturn, failed, installationReturn, manage, next, router]);
  return <Surface className="form-page"><PageHeading title="GitHub repo izinleri" description="FIRST yalnızca GitHub’da seçtiğiniz repolara erişir. İlk bağlantıda izinleri tamamlayın; sonraki paylaşımlarda reponuzu kayıtlı listeden seçin. Listeyi yalnızca istediğinizde yenilersiniz."/>
    {error && <Alert role="alert" tone="error">{error}</Alert>}
    {state === 'loading' && <Alert role="status">GitHub bağlantınız kontrol ediliyor…</Alert>}
    {state === 'login' && <Alert><p>Devam etmek için GitHub ile giriş yapın.</p><ActionLink href="/giris">Giriş yap</ActionLink></Alert>}
    {state === 'link' && <Alert><p>Önce hesabınıza GitHub hesabınızı bağlayın. Repo izinleri ardından aynı akışta tamamlanır.</p><ActionLink href="/hesap">Hesabıma git</ActionLink></Alert>}
    {state === 'disabled' && <Alert>GitHub repo bağlantısı şu anda kullanılamıyor. Daha sonra tekrar deneyebilirsiniz.</Alert>}
    {state === 'retry' && <Button onClick={() => {navigating.current = false; setError(''); setState('loading'); setAttempt(value => value + 1);}}>İzinleri tamamlamayı yeniden dene</Button>}
    {state === 'repositories' && <Alert>
      <p>{installationReturn ? 'GitHub izinlerinden döndünüz. Son değişiklikleri almak için kayıtlı repo listenizi yenileyin.' : cache === null ? 'Repo izinlerini yönetebilir, bağlantıyı yeniden yetkilendirebilir veya kayıtlı listeyi isteğinizle yenileyebilirsiniz.' : cache.repositories.length ? `${cache.repositories.length} repo kayıtlı listenizde bulunuyor.` : 'Kayıtlı listenizde henüz repo yok. GitHub izinlerini tamamladıysanız listeyi yenileyin; kurulum onayı bekleniyorsa onaylandıktan sonra tekrar deneyin.'}</p>
      <p className="field-help">{cache ? `${repositoryCacheCaption(cache.cached_at ?? null)}. Liste siz yenileyene kadar korunur.` : 'Kayıtlı liste bu ekranda henüz yüklenmedi; otomatik yenileme yapılmaz.'}</p>
      {installation && <Button variant="secondary" disabled={refreshing||authorizing} onClick={() => {if(navigating.current||refreshLock.current)return;try {navigating.current=true;store(nextKey, destination); navigateToGitHub(installation, true);} catch (caught) {navigating.current=false;setError((caught as Error).message);}}}>Repo izinlerini yönet</Button>}
      <p className="field-help">GitHub izni kaldırıldıysa veya liste yenilenemiyorsa bağlantıyı yeniden yetkilendirin.</p>
      <Button variant="secondary" loading={authorizing} disabled={refreshing} onClick={async () => {
        if(navigating.current || refreshLock.current) return;
        navigating.current = true; setAuthorizing(true); setError('');
        try {
          store(nextKey,destination); store(manageKey,'1');
          const result = await api<{authorization_url:string}>('projects/github/start',{return_to:destination});
          navigateToGitHub(result.authorization_url);
        } catch(caught) {navigating.current = false; setAuthorizing(false); setError((caught as Error).message);}
      }}>GitHub bağlantısını yeniden yetkilendir</Button>
      <Button variant="secondary" loading={refreshing} disabled={authorizing} onClick={async () => {
        if(refreshLock.current || navigating.current) return;
        refreshLock.current = true; setRefreshing(true); setError('');
        try {setCache(await api<RepositoryCache>('projects/github/repositories',{}));}
        catch(caught) {setError((caught as Error).message);}
        finally {refreshLock.current = false; setRefreshing(false);}
      }}>Repo listesini yenile</Button>
      {(cache === null || !!cache.repositories.length) && <Button disabled={refreshing||authorizing} onClick={() => {if(navigating.current||refreshLock.current)return;store(nextKey, null); store(manageKey, null); router.replace(destination); router.refresh();}}>{cache ? 'Kayıtlı repolarla devam et' : 'Devam et'}</Button>}
    </Alert>}
    <p><ActionLink variant="quiet" href="/hesap">Hesabıma dön</ActionLink></p>
  </Surface>;
}
