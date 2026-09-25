'use client';

import {useEffect, useRef, useState} from 'react';
import {api, publicProjectFeed} from '../lib/api';
import type {ProjectPage, ProjectConfig} from '../lib/projects';
import {HomeProjectRow} from './home-project-row';
import {HomeNavigation} from './home-navigation';
import {RepositoryMark} from './project-card';
import {useSession} from './session-provider';
import {ActionLink, Alert, Button, Field, Input, Select, PageHeading, Surface} from './ui';

const emptyFilters = {q:'', technology:'', skill:'', category:'', subcategory:'', stage:'', need_type:'', participation_mode:''};
type FilterKey = keyof typeof emptyFilters;
const primaryFilterKeys: FilterKey[] = ['category', 'stage', 'need_type'];

export function HomePage() {
  const {status, user} = useSession();
  const [search, setSearch] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [config, setConfig] = useState<ProjectConfig | null>(null);
  const [configError, setConfigError] = useState('');
  const [filters, setFilters] = useState(emptyFilters);
  const [retry, setRetry] = useState(0);
  const [feed, setFeed] = useState<ProjectPage | null>(null);
  const [error, setError] = useState('');
  const feedHeading = useRef<HTMLHeadingElement>(null);
  const focusOnLoad = useRef(false);

  useEffect(() => {
    let active = true;
    api<ProjectConfig>('projects/config')
      .then(data => {if(active) setConfig(data);})
      .catch(error => {if(active) setConfigError((error as Error).message);});
    return () => {active = false;};
  }, []);

  function filter(key: FilterKey, value: string) {
    setFeed(null);
    setError('');
    setFilters(previous => ({...previous, [key]:value, ...(key === 'category' ? {subcategory:''} : {})}));
    setPage(1);
  }

  function clearFilters() {
    setFeed(null);
    setError('');
    setSearch('');
    setFilters({...emptyFilters});
    setPage(1);
  }

  function changePage(next: number) {
    setFeed(null);
    setError('');
    focusOnLoad.current = true;
    setPage(next);
  }

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const query = new URLSearchParams({page:String(page)});
    Object.entries(filters).forEach(([key, value]) => {if(value) query.set(key, value);});
    void publicProjectFeed<ProjectPage>(query, controller.signal)
      .then(data => {if(active) setFeed(data);})
      .catch(caught => {if(active && !controller.signal.aborted) setError((caught as Error).message);});
    return () => {active = false; controller.abort();};
  }, [page, retry, filters]);

  useEffect(() => {
    if(feed && focusOnLoad.current) {
      feedHeading.current?.focus();
      focusOnLoad.current = false;
    }
  }, [feed]);

  const filterOptions = [
    ['category', 'Kategori', config?.categories || []],
    ['stage', 'Proje aşaması', config?.stages || []],
    ['need_type', 'Aranan katkı', config?.need_types || []],
    ['technology', 'Teknoloji', config?.technologies || []],
    ['skill', 'Aranan beceri', config?.skills || []],
    ['subcategory', 'Alt kategori', config?.categories.find(item => item.value === filters.category)?.subcategories || []],
    ['participation_mode', 'Katılım yöntemi', config?.participation_modes || []],
  ] as const;
  const activeFilters = Object.entries(filters).filter(([, value]) => value);
  const extraFilterCount = activeFilters.filter(([key]) => key !== 'q' && !primaryFilterKeys.includes(key as FilterKey)).length;

  return <div className="home-discovery">
    <HomeNavigation/>
    <div className="home-intro" id="home-content" tabIndex={-1}>
      <PageHeading eyebrow="" title="Katkına açık projeler" description="Bir proje seç. Birlikte üretmeye başla."/>
      {status === 'ready' && user && <div className="community-actions">
        <ActionLink href="/projelerim/yeni">Proje paylaş</ActionLink>
        <ActionLink href="/projelerim" variant="secondary">Projelerim</ActionLink>
      </div>}
    </div>
    {status === 'ready' && user && !user.email_verified && <Alert><p>Proje paylaşmak için e-posta adresinizi doğrulayın. <a href="/hesap">Hesap ayarlarına git</a></p></Alert>}
    {configError && <Alert role="alert" tone="error">
      <p>Filtre seçenekleri yüklenemedi: {configError}</p>
      <Button variant="secondary" onClick={async () => {
        try {setConfig(await api<ProjectConfig>('projects/config')); setConfigError('');}
        catch(error) {setConfigError((error as Error).message);}
      }}>Filtreleri yeniden yükle</Button>
    </Alert>}
    <div className="home-filters">
      <div className="home-search-toolbar">
        <form className="home-search" role="search" aria-label="Proje ara" onSubmit={event => {event.preventDefault(); filter('q', search.trim());}}>
          <Field id="project-search" label="Proje ara" className="home-search-field">
            <span className="home-search-icon" aria-hidden="true"/>
            <Input id="project-search" type="search" maxLength={100} value={search} onChange={event => setSearch(event.target.value)} placeholder="Proje adı veya açıklamada ara"/>
          </Field>
          <Button type="submit">Ara</Button>
        </form>
        {config && <Button variant="secondary" aria-expanded={filtersOpen} aria-controls="discovery-options" onClick={() => setFiltersOpen(value => !value)}>
          <span className="home-filter-icon" aria-hidden="true"/>
          Filtreler{extraFilterCount > 0 && <span className="count-badge" aria-label={`${extraFilterCount} ek filtre etkin`}>{extraFilterCount}</span>}
        </Button>}
      </div>
      {config && <>
        <div className="home-primary-filters">
          {filterOptions.filter(([key]) => primaryFilterKeys.includes(key)).map(([key, label, options]) => <Field key={key} id={`filter-${key}`} label={label}>
            <Select id={`filter-${key}`} value={filters[key]} onChange={event => filter(key, event.target.value)}>
              <option value="">Tümü</option>
              {options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </Select>
          </Field>)}
        </div>
        <div id="discovery-options" className="home-extra-filters" hidden={!filtersOpen}>
          {filterOptions.filter(([key]) => !primaryFilterKeys.includes(key)).map(([key, label, options]) => <Field key={key} id={`filter-${key}`} label={label}>
            <Select id={`filter-${key}`} value={filters[key]} disabled={key === 'subcategory' && !filters.category} onChange={event => filter(key, event.target.value)}>
              <option value="">Tümü</option>
              {options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </Select>
          </Field>)}
        </div>
      </>}
      {activeFilters.length > 0 && <div className="home-filter-summary">
        <div className="active-filters" aria-label="Etkin filtreler">
          {activeFilters.map(([key, value]) => {
            const option = filterOptions.find(([filterKey]) => filterKey === key)?.[2].find(item => item.value === value);
            const label = key === 'q' ? `Arama: ${value}` : option?.label || value;
            return <Button key={key} variant="quiet" aria-label={`${label} filtresini kaldır`} onClick={() => {filter(key as FilterKey, ''); if(key === 'q') setSearch('');}}>
              {label} <span aria-hidden="true">×</span>
            </Button>;
          })}
        </div>
        <Button variant="quiet" onClick={clearFilters}>Filtreleri temizle</Button>
      </div>}
    </div>
    <section className="community-feed" aria-labelledby="feed-heading" aria-busy={!feed && !error}>
      <div className="home-feed-toolbar">
        <h2 id="feed-heading" tabIndex={-1} ref={feedHeading}>{feed ? `${feed.count.toLocaleString('tr-TR')} proje` : 'Projeler'}</h2>
        <span className="feed-sort">En yeni paylaşımlar</span>
      </div>
      {!feed && !error && <div className="feed-loading" role="status"><span className="loading-dot" aria-hidden="true"/>Projeler yükleniyor…</div>}
      {error && <Alert tone="error" role="alert">
        <p>{error}</p>
        <Button variant="secondary" onClick={() => {setError(''); setFeed(null); setRetry(value => value + 1);}}>Yeniden dene</Button>
        {page > 1 && <Button variant="quiet" onClick={() => changePage(1)}>İlk sayfaya dön</Button>}
      </Alert>}
      {feed && <>
        {feed.projects.length ? <div className="home-project-list">{feed.projects.map(project => <HomeProjectRow key={project.id} project={project}/>)}</div> : <Surface className="empty-state">
          <RepositoryMark/>
          <h3>{feed.count === 0 ? 'Bu filtrelerle ilan bulunamadı.' : 'Bu sayfada proje bulunamadı.'}</h3>
          <p>{feed.count === 0 ? 'Filtreleri değiştirebilir veya kendi projenizi paylaşabilirsiniz.' : 'Paylaşımlar değişmiş olabilir. İlk sayfadan devam edebilirsiniz.'}</p>
          {feed.count === 0 ? (status === 'ready' && <ActionLink href={user ? '/projelerim/yeni' : '/kayit'}>{user ? 'İlk projeyi paylaş' : 'Hesap oluştur'}</ActionLink>) : <Button onClick={() => changePage(1)}>İlk sayfaya dön</Button>}
        </Surface>}
        {(feed.previous_page || feed.next_page) && <nav className="pagination" aria-label="Proje sayfaları">
          <Button variant="secondary" disabled={!feed.previous_page} onClick={() => {if(feed.previous_page) changePage(feed.previous_page);}}>← Önceki</Button>
          <span aria-live="polite">Sayfa {page}</span>
          <Button variant="secondary" disabled={!feed.next_page} onClick={() => {if(feed.next_page) changePage(feed.next_page);}}>Sonraki →</Button>
        </nav>}
      </>}
    </section>
  </div>;
}
