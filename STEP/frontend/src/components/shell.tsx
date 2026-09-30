"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useSession } from "./session";
import { Action, Notice } from "./ui";
const links = [["/jobs","İlanlar"],["/people","Öğrenciler"],["/dashboard","Çalışma alanım"],["/employer","İlanlarım"],["/applications","Başvurularım"],["/teams","Takımlar"],["/contracts","Sözleşmeler"],["/credits","Krediler"],["/money","Ödeme ve kazanç"],["/messages","Mesajlar"],["/notifications","Bildirimler"],["/support","Destek"],["/account","Profil ve doğrulama"]];
export function Shell({ children }: { children: ReactNode }) { const pathname = usePathname();
  const { user, config, error, refresh } = useSession(); return <>
<a className="skip-link" href="#main-content">İçeriğe geç</a>
<header className="site-header">
<Link href="/" className="brand">STEP <span>Öğrenci iş pazarı</span>
</Link>
<div className="header-actions">{user ? <>
<span>{user.display_name}</span>
<Action path="auth/logout/" label="Çıkış yap" message="Oturum kapatıldı." onSuccess={() => { void refresh(); }} />
</> : <>
<Link href="/auth/login">Giriş yap</Link>
<Link className="button button-small" href="/auth/register">Kayıt ol</Link>
</>}</div>
</header>
<div className="app-layout">
<nav className="sidebar" aria-label="Ana gezinme">{links.filter(([path]) => user || ["/jobs","/people"].includes(path)).map(([path,label]) => <Link key={path} href={path} aria-current={pathname === path || pathname.startsWith(`${path}/`) ? "page" : undefined}>{label}</Link>)}{user?.is_staff ? <Link href="/admin" aria-current={pathname.startsWith("/admin") ? "page" : undefined}>Yönetim</Link> : null}</nav>
<main id="main-content" className="main-content">{error ? <Notice tone="error">STEP bağlantısı kurulamadı: {error}<button className="text-button" onClick={() => { void refresh(); }}>Yeniden bağlan</button>
</Notice> : null}{config && config.mode !== "live" ? <Notice tone="warning">Deneme ortamı. Buradaki ödemeler ve bakiyeler canlı kazanç veya gerçek banka aktarımı değildir.{config.payment_provider === "simulator" ? " Yerel ödeme simülasyonu kullanılıyor." : " Sağlayıcının test bağlantısı kullanılıyor."}</Notice> : null}{children}</main>
</div>
<footer className="site-footer">STEP · İş bedeli TL, platform işlemleri krediyle. Freelancer iş bedelinden %10 komisyon alınır.</footer>
</>; }
