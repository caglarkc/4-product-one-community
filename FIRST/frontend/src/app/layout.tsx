import Link from 'next/link';
import './globals.css';
export const metadata={title:'FIRST',description:'FIRST topluluk hesabı',robots:{index:false,follow:false}};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="tr"><body><a className="skip" href="#main">İçeriğe geç</a><header><Link href="/">FIRST</Link><nav aria-label="Ana gezinme"><Link href="/giris">Giriş</Link><Link href="/kayit">Kayıt</Link><Link href="/hesap">Hesabım</Link></nav></header><main id="main">{children}</main></body></html>;}
