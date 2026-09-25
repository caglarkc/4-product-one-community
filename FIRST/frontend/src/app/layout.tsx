import Link from 'next/link';
import { SessionNavigation, SessionProvider } from '../components/session-provider';
import './globals.css';
import './home-discovery.css';

export const metadata = { title: 'FIRST', description: 'FIRST — topluluğun geliştirdiği projeler ve birlikte üretmek için bir alan', robots: { index: false, follow: false } };

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="tr"><body><SessionProvider>
    <a className="skip" href="#main">İçeriğe geç</a>
    <a className="skip home-skip" href="#home-content">İçeriğe geç</a>
    <header className="site-header"><div className="header-inner">
      <Link className="brand" href="/" aria-label="FIRST ana sayfa">
        <span className="brand-mark" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" focusable="false">
            <path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        FIRST
      </Link>
      <SessionNavigation/>
    </div></header>
    <main id="main">{children}</main>
    <footer className="site-footer"><div className="footer-inner"><div><strong>FIRST Topluluğu</strong><p>Projeleri keşfet, toplulukla birlikte üret.</p></div><nav aria-label="Alt gezinme"><Link href="/">Projeler</Link><Link href="/kisiler">Kişiler</Link></nav></div></footer>
  </SessionProvider></body></html>;
}
