'use client';
import {useEffect, useRef, useState} from 'react';
import {api,publicProjectFeed} from '../lib/api';
import type {ProjectPage,ProjectConfig} from '../lib/projects';
import {ProjectCard, RepositoryMark} from './project-card';
import {useSession} from './session-provider';
import {ActionLink, Alert, Button, Field, Input, Select, PageHeading, Surface} from './ui';

export function HomePage() {
  const {status, user} = useSession();
  const [search,setSearch]=useState('');
  const [filtersOpen,setFiltersOpen]=useState(false);
  const [page, setPage] = useState(1);
  const [config,setConfig]=useState<ProjectConfig|null>(null);const [configError,setConfigError]=useState('');const [filters,setFilters]=useState({q:'',technology:'',skill:'',category:'',subcategory:'',stage:'',need_type:'',participation_mode:''});
  useEffect(()=>{let active=true;api<ProjectConfig>('projects/config').then(data=>{if(active)setConfig(data);}).catch(error=>{if(active)setConfigError((error as Error).message);});return()=>{active=false;};},[]);
  function filter(key:keyof typeof filters,value:string){setFeed(null);setError('');setFilters(previous=>({...previous,[key]:value,...(key==='category'?{subcategory:''}:{})}));setPage(1);}

  const feedHeading = useRef<HTMLHeadingElement>(null);
  const focusOnLoad = useRef(false);
  function changePage(next:number) {setFeed(null);setError('');focusOnLoad.current = true; setPage(next);}
  const [retry, setRetry] = useState(0);
  const [feed, setFeed] = useState<ProjectPage | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const query = new URLSearchParams({page:String(page)});
    Object.entries(filters).forEach(([key,value])=>{if(value)query.set(key,value);});
    void publicProjectFeed<ProjectPage>(query,controller.signal)
      .then(data => {if(active) setFeed(data);})
      .catch(caught => {if(active && !controller.signal.aborted) setError((caught as Error).message);});
    return () => {active = false; controller.abort();};
  }, [page,retry,filters]);
  useEffect(() => {if(feed && focusOnLoad.current) {feedHeading.current?.focus(); focusOnLoad.current = false;}}, [feed]);
  const filterOptions = [
    ['technology', 'Teknoloji', config?.technologies || []],
    ['skill', 'Aranan beceri', config?.skills || []],
    ['category', 'Üst kategori', config?.categories || []],
    ['subcategory', 'Alt kategori', config?.categories.find(item => item.value === filters.category)?.subcategories || []],
    ['stage', 'Proje aşaması', config?.stages || []],
    ['need_type', 'Aranan katkı', config?.need_types || []],
    ['participation_mode', 'Katılım yöntemi', config?.participation_modes || []],
  ] as const;
  return <div className="community-page">
    <div className="community-intro"><PageHeading eyebrow="" title="Projeleri Keşfet" description="Toplulukla birlikte açık kaynak ve ekip projeleri üretin."/>
      {status === 'ready' && <div className="community-actions"><ActionLink href={user?'/projelerim/yeni':'/kayit'}>{user?'Proje paylaş':'Topluluğa katıl'}</ActionLink>{user && <ActionLink href="/projelerim" variant="secondary">Projelerim</ActionLink>}</div>}
    </div>
    {status === 'ready' && user && !user.email_verified && <Alert><p>Proje paylaşmak için e-posta adresinizi doğrulayın. <a href="/hesap">Hesap ayarlarına git</a></p></Alert>}
    {configError&&<Alert role="alert" tone="error"><p>Filtre seçenekleri yüklenemedi: {configError}</p><Button variant="secondary" onClick={async()=>{try{setConfig(await api<ProjectConfig>('projects/config'));setConfigError('');}catch(error){setConfigError((error as Error).message);}}}>Filtreleri yeniden yükle</Button></Alert>}
    {config&&<Surface className="project-panel discovery-filters"><form className="community-search" onSubmit={event=>{event.preventDefault();filter('q',search.trim());}}><Field id="project-search" label="Proje ara"><Input id="project-search" type="search" maxLength={100} value={search} onChange={event=>setSearch(event.target.value)} placeholder="Proje adı veya açıklamada ara…"/></Field><Button type="submit">Ara</Button></form><Button variant="secondary" aria-expanded={filtersOpen} aria-controls="discovery-options" onClick={()=>setFiltersOpen(value=>!value)}>Filtreler <span className="count-badge">{Object.values(filters).filter(Boolean).length || 'Tümü'}</span></Button><div id="discovery-options" className="listing-filters discovery-options" hidden={!filtersOpen}>{filterOptions.map(([key,label,options])=><Field key={key} id={`filter-${key}`} label={label}><Select id={`filter-${key}`} value={filters[key]} disabled={key==='subcategory'&&!filters.category} onChange={event=>filter(key,event.target.value)}><option value="">Tümü</option>{options.map(option=><option key={option.value} value={option.value}>{option.label}</option>)}</Select></Field>)}</div><div className="filter-summary"><div className="active-filters">{Object.entries(filters).filter(([,value])=>value).map(([key,value])=>{const option=filterOptions.find(([filterKey])=>filterKey===key)?.[2].find(item=>item.value===value);const label=key==='q'?`Arama: ${value}`:option?.label||value;return <Button key={key} variant="quiet" aria-label={`${label} filtresini kaldır`} onClick={()=>{filter(key as keyof typeof filters,'');if(key==='q')setSearch('');}}>{label} <span aria-hidden="true">×</span></Button>;})}</div><Button variant="quiet" onClick={()=>{setFeed(null);setError('');setSearch('');setFilters({q:'',technology:'',skill:'',category:'',subcategory:'',stage:'',need_type:'',participation_mode:''});setPage(1);}}>Filtreleri temizle</Button><p className="field-help">{feed ? `${feed.count.toLocaleString('tr-TR')} sonuç listeleniyor` : 'Herkese açık ve başvuru alan ilanlar'}</p></div></Surface>}
    <section className="community-feed" aria-labelledby="feed-heading" aria-busy={!feed&&!error}>
      <div className="feed-toolbar"><div className="feed-title"><RepositoryMark/><h2 id="feed-heading" tabIndex={-1} ref={feedHeading}>Topluluk projeleri</h2>{feed && <span className="count-badge" aria-label={`${feed.count} aktif proje`}>{feed.count.toLocaleString('tr-TR')}</span>}</div><span className="feed-sort">En yeni paylaşımlar</span></div>
      {!feed && !error && <div className="feed-loading" role="status"><span className="loading-dot" aria-hidden="true"/>Projeler yükleniyor…</div>}
      {error && <Alert tone="error" role="alert"><p>{error}</p><Button variant="secondary" onClick={() => {setError('');setFeed(null);setRetry(value => value + 1);}}>Yeniden dene</Button>{page>1&&<Button variant="quiet" onClick={()=>changePage(1)}>İlk sayfaya dön</Button>}</Alert>}
      {feed && <>
        {feed.projects.length ? <div className="repository-grid">{feed.projects.map(project => <ProjectCard key={project.id} project={project}/>)}</div> : <Surface className="empty-state"><RepositoryMark/><h3>{feed.count===0?'Bu filtrelerle ilan bulunamadı.':'Bu sayfada proje bulunamadı.'}</h3><p>{feed.count===0?'Filtreleri değiştirebilir veya kendi projenizi paylaşabilirsiniz.':'Paylaşımlar değişmiş olabilir. İlk sayfadan devam edebilirsiniz.'}</p>{feed.count===0?(status==='ready'&&<ActionLink href={user?'/projelerim/yeni':'/kayit'}>{user?'İlk projeyi paylaş':'Hesap oluştur'}</ActionLink>):<Button onClick={()=>changePage(1)}>İlk sayfaya dön</Button>}</Surface>}
        {(feed.previous_page || feed.next_page) && <nav className="pagination" aria-label="Proje sayfaları"><Button variant="secondary" disabled={!feed.previous_page} onClick={() => {if(feed.previous_page) changePage(feed.previous_page);}}>← Önceki</Button><span aria-live="polite">Sayfa {page}</span><Button variant="secondary" disabled={!feed.next_page} onClick={() => {if(feed.next_page) changePage(feed.next_page);}}>Sonraki →</Button></nav>}
      </>}
    </section>
  </div>;
}
