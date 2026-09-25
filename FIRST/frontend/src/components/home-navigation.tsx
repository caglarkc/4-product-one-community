import Link from 'next/link';

const links = [
  ['/', 'Projeler', 'folder'],
  ['/ekipler', 'Ekipler', 'user-group'],
  ['/gorevler', 'Görevler', 'clipboard-document-check'],
  ['/kisiler', 'Kişiler', 'user'],
] as const;

export function HomeNavigation() {
  return <aside className="home-sidebar">
    <Link className="brand" href="/" aria-label="FIRST ana sayfa">
      <span className="brand-mark" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" focusable="false">
          <path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </span>FIRST
    </Link>
    <nav aria-label="Proje keşfi gezinmesi">
      {links.map(([href,label,icon]) => <Link key={href} href={href} aria-current={href === '/' ? 'page' : undefined}>
        <span className="home-nav-icon" style={{maskImage:`url(/icons/heroicons/${icon}.svg)`}} aria-hidden="true"/>
        {label}
      </Link>)}
    </nav>
  </aside>;
}
