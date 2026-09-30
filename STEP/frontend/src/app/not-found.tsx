import Link from "next/link";
export default function NotFound() { return <section className="panel">
<h1>Sayfa bulunamadı</h1>
<p>Bağlantı değişmiş veya sayfa kaldırılmış olabilir.</p>
<Link href="/jobs">İlanlara dön</Link>
</section>; }
