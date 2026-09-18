import Link from 'next/link';
import { ActionLink } from '../components/ui';
import './globals.css';

export const metadata = { title: 'FIRST', description: 'FIRST topluluk hesabı', robots: { index: false, follow: false } };

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="tr"><body>
    <a className="skip" href="#main">İçeriğe geç</a>
    <header className="site-header"><div className="header-inner">
      <Link className="brand" href="/" aria-label="FIRST ana sayfa"><span className="brand-mark" aria-hidden="true">f</span>FIRST</Link>
      <nav className="site-nav" aria-label="Ana gezinme">
        <ActionLink variant="quiet" href="/giris">Giriş</ActionLink>
        <ActionLink variant="quiet" href="/hesap">Hesabım</ActionLink>
        <ActionLink variant="secondary" href="/kayit">Kayıt</ActionLink>
      </nav>
    </div></header>
    <main id="main">{children}</main>
    <footer className="site-footer"><span>FIRST · Birlikte üretmek için.</span><span>Future Innovators Research &amp; Source Team</span></footer>
  </body></html>;
}
