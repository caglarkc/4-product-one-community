'use client';
import {useEffect, useRef, useState} from 'react';
import {api, ApiError} from '../lib/api';
import type {ProjectPage} from '../lib/projects';
import {ProjectCard, RepositoryMark} from './project-card';
import {useSession} from './session-provider';
import {ActionLink, Alert, Button, PageHeading, Surface} from './ui';

export function HomePage() {
  const {status, user} = useSession();
  const [page, setPage] = useState(1);
  const feedHeading = useRef<HTMLHeadingElement>(null);
  const focusOnLoad = useRef(false);
  function changePage(next:number) {focusOnLoad.current = true; setPage(next);}
  const [retry, setRetry] = useState(0);
  const [feed, setFeed] = useState<ProjectPage | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    setFeed(null); setError('');
    async function load() {
      const query = new URLSearchParams({page:String(page)});
      try {return await api<ProjectPage>('projects',undefined,'GET',query);}
      catch(caught) {
        // A public list remains available after an expired bearer is cleared.
        if(caught instanceof ApiError && ['invalid_session','session_changed'].includes(caught.code || '')) return api<ProjectPage>('projects',undefined,'GET',query);
        throw caught;
      }
    }
    void load().then(data => {if(active) setFeed(data);}).catch(caught => {if(active) setError((caught as Error).message);});
    return () => {active = false;};
  }, [page,retry]);
  useEffect(() => {if(feed && focusOnLoad.current) {feedHeading.current?.focus(); focusOnLoad.current = false;}}, [feed]);
  return <div className="community-page">
    <div className="community-intro"><PageHeading eyebrow="FIRST / TOPLULUK" title="Birlikte geliştirilecek projeleri keşfet." description="Topluluğun üzerinde çalıştığı projelere göz atın. Kendi projenizi paylaşın, bir sonraki fikrinize alan açın."/>
      {status === 'ready' && <div className="community-actions"><ActionLink href={user?'/projelerim/yeni':'/kayit'}>{user?'Proje paylaş':'Topluluğa katıl'}</ActionLink>{user && <ActionLink href="/projelerim" variant="secondary">Projelerim</ActionLink>}</div>}
    </div>
    {status === 'ready' && user && !user.email_verified && <Alert><p>Proje paylaşmak için e-posta adresinizi doğrulayın. <a href="/hesap">Hesap ayarlarına git</a></p></Alert>}
    <section className="community-feed" aria-labelledby="feed-heading" aria-busy={!feed&&!error}>
      <div className="feed-toolbar"><div className="feed-title"><RepositoryMark/><h2 id="feed-heading" tabIndex={-1} ref={feedHeading}>Topluluk projeleri</h2>{feed && <span className="count-badge" aria-label={`${feed.count} aktif proje`}>{feed.count.toLocaleString('tr-TR')}</span>}</div><span className="feed-sort">En yeni paylaşımlar</span></div>
      {!feed && !error && <div className="feed-loading" role="status"><span className="loading-dot" aria-hidden="true"/>Projeler yükleniyor…</div>}
      {error && <Alert tone="error" role="alert"><p>{error}</p><Button variant="secondary" onClick={() => setRetry(value => value + 1)}>Yeniden dene</Button>{page>1&&<Button variant="quiet" onClick={()=>changePage(1)}>İlk sayfaya dön</Button>}</Alert>}
      {feed && <>
        {feed.projects.length ? <div className="repository-grid">{feed.projects.map(project => <ProjectCard key={project.id} project={project}/>)}</div> : <Surface className="empty-state"><RepositoryMark/><h3>{feed.count===0?'İlk paylaşım için yer hazır.':'Bu sayfada proje bulunamadı.'}</h3><p>{feed.count===0?'Toplulukta henüz aktif bir proje paylaşılmadı. Kendi çalışmanızla ilk adımı atabilirsiniz.':'Paylaşımlar değişmiş olabilir. İlk sayfadan devam edebilirsiniz.'}</p>{feed.count===0?(status==='ready'&&<ActionLink href={user?'/projelerim/yeni':'/kayit'}>{user?'İlk projeyi paylaş':'Hesap oluştur'}</ActionLink>):<Button onClick={()=>changePage(1)}>İlk sayfaya dön</Button>}</Surface>}
        {(feed.previous_page || feed.next_page) && <nav className="pagination" aria-label="Proje sayfaları"><Button variant="secondary" disabled={!feed.previous_page} onClick={() => {if(feed.previous_page) changePage(feed.previous_page);}}>← Önceki</Button><span aria-live="polite">Sayfa {page}</span><Button variant="secondary" disabled={!feed.next_page} onClick={() => {if(feed.next_page) changePage(feed.next_page);}}>Sonraki →</Button></nav>}
      </>}
    </section>
  </div>;
}
