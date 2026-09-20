import Link from 'next/link';
import { SessionNavigation, SessionProvider } from '../components/session-provider';
import './globals.css';

export const metadata = { title: 'FIRST', description: 'FIRST topluluk hesabı', robots: { index: false, follow: false } };

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="tr"><body><SessionProvider>
    <a className="skip" href="#main">İçeriğe geç</a>
    <header className="site-header"><div className="header-inner">
      <Link className="brand" href="/" aria-label="FIRST ana sayfa">
        <span className="brand-mark" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" focusable="false">
            <path d="M5 16V4H15M5 10H12" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        FIRST
      </Link>
      <SessionNavigation/>
    </div></header>
    <main id="main">{children}</main>
    <footer className="site-footer"><span>FIRST · Birlikte üretmek için.</span><span>Future Innovators Research &amp; Source Team</span></footer>
  </SessionProvider></body></html>;
}
