"use client";
import Link from "next/link";
import { useSession } from "@/components/session";
import { Auth, Heading, Panel, State, Status, usePaged, Pager } from "@/components/ui";
import { money } from "@/lib/api";
import type { Contract, Job } from "@/lib/types";
export function Home() { const jobs = usePaged<Job>("jobs/"); return <>
<Heading title="Üniversiteden işe" description="Üniversite öğrencileriyle sabit ücretli veya saatlik çalışın. İlanları inceleyin, teklif verin ve işinizi STEP çalışma alanında yürütün." action={<Link className="button" href="/auth/register">STEP'e katıl</Link>} />
<div className="grid">
<Panel title="Öğrenciler için">
<p>Becerilerinizi ve portföy bağlantılarınızı paylaşın. Bireysel veya takım olarak işlere teklif verin.</p>
<Link href="/jobs">İlanları incele</Link>
</Panel>
<Panel title="İşverenler için">
<p>İşi ve beklenen sonucu açıklayın. Öğrenci veya takım seçin; çalışma başlamadan ilgili aşamayı ya da haftayı fonlayın.</p>
<Link href="/employer">İlan oluştur</Link>
</Panel>
</div>
<Panel title="Başvuruya açık ilanlar">
<State loading={jobs.loading} error={jobs.error} empty={!jobs.items.length} retry={jobs.reload}>
<div className="card-list">{jobs.items.map(job => <article className="card" key={job.id}>
<h3>
<Link href={`/jobs/${job.id}`}>{job.title}</Link>
</h3>
<div className="meta">
<Status value={job.work_type} />
<span>{money(job.budget)}</span>
<span>{job.expected_duration}</span>
</div>
<p>{job.description.slice(0, 260)}{job.description.length > 260 ? "…" : ""}</p>
</article>)}</div>
<Pager {...jobs} />
</State>
</Panel>
</>; }
const areas = [["/employer","İlanlarım","İlan yayınlama, başvuru değerlendirme ve davet."],["/applications","Başvurularım","Teklifler, davetler ve sözleşmeye geçiş."],["/teams","Takımlar","Üyeler, liderlik ve ayrı takım kredisi."],["/credits","Krediler","Bakiye, satın alma ve öne çıkarma."],["/messages","Mesajlar","İlgili iş ve başvuruların görüşmeleri."],["/money","Ödeme ve kazanç","Fonlama, serbest bırakma ve banka çekim talepleri."]];
export function Dashboard() { const { user } = useSession();
  const contracts = usePaged<Contract>(user ? "contracts/" : null); return <Auth>
<Heading title="Çalışma alanım" description={user ? `${user.display_name}, işlerinizi ve bekleyen işlemlerinizi buradan yönetebilirsiniz.` : undefined} />
<div className="grid grid-three">{areas.map(([path,title,description]) => <Panel key={path} title={title}>
<p>{description}</p>
<Link href={path}>Aç</Link>
</Panel>)}</div>
<Panel title="Sözleşmelerim">
<State loading={contracts.loading} error={contracts.error} empty={!contracts.items.length} retry={contracts.reload}>{contracts.items.map(contract => <article className="card" key={contract.id}>
<h3>
<Link href={`/contracts/${contract.id}`}>{contract.job_title || contract.scope.slice(0, 90)}</Link>
</h3>
<Status value={contract.status} />
<p>{contract.expected_duration}</p>
</article>)}<Pager {...contracts} />
</State>
</Panel>
</Auth>; }
