"use client";
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <section className="panel">
<h1>Sayfa açılamadı</h1>
<p role="alert">İşlem yarıda kalmış olabilir. Ödeme yaptıysanız yeniden ödeme başlatmadan önce ödeme geçmişinden sonucu kontrol edin.</p>
<button className="button" onClick={reset}>Sayfayı yeniden aç</button>
</section>; }
