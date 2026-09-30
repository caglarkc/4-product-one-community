import type { Metadata } from "next";
import type { ReactNode } from "react";
import { SessionProvider } from "@/components/session";
import { Shell } from "@/components/shell";
import "./globals.css";
export const metadata: Metadata = { title: { default: "STEP — Öğrenci iş pazarı", template: "%s | STEP" }, description: "Üniversite öğrencileri için sabit ücretli ve saatlik iş, teklif ve çalışma alanı.", robots: { index: false, follow: false } };
export default function RootLayout({ children }: { children: ReactNode }) { return <html lang="tr">
<body>
<SessionProvider>
<Shell>{children}</Shell>
</SessionProvider>
</body>
</html>; }
