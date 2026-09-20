import Link from 'next/link';
import type {ProjectSummary} from '../lib/projects';
import {ActionLink, Surface} from './ui';

export function RepositoryMark() {
  return <svg className="repository-mark" width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false"><path d="M5 4h13v16H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2ZM4 17h14M8 8h6M8 11h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>;
}
export function ProjectCard({project, manage = false, active, heading = 'h3'}: {project: ProjectSummary; manage?: boolean; active?: boolean; heading?: 'h2' | 'h3'}) {
  const Heading = heading;
  const date = new Date(project.updated_at);
  const dateLabel = Number.isNaN(date.getTime()) ? null : new Intl.DateTimeFormat('tr-TR', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'}).format(date);
  return <Surface className="repository-card">
    <div className="repository-card-title"><RepositoryMark/><Heading><Link className="repository-card-link" href={`/projeler/${project.id}`}>{project.title}</Link></Heading>{active !== undefined && <span className={`connection-status${active?' connection-status--connected':''}`}>{active?'Paylaşım aktif':'Arşivde'}</span>}</div>
    <p className="repository-description">{project.description || 'Bu proje için henüz bir açıklama eklenmedi.'}</p>
    <dl className="repository-topics"><div><dt>Üst kategori</dt><dd>{project.category_label || 'Belirtilmedi'}</dd></div><div><dt>Alt kategori</dt><dd>{project.subcategory_label || 'Belirtilmedi'}</dd></div></dl>
    <dl className="repository-topics"><div><dt>Aranan katkı</dt><dd>{project.need_type_label || 'Belirtilmedi'}</dd></div><div><dt>Katılım</dt><dd>{project.participation_mode_label || 'Belirtilmedi'}</dd></div></dl>
    <div className="repository-card-meta"><span className="project-stage"><span className="stage-dot" aria-hidden="true"/>{project.stage_label || 'Proje durumu belirtilmedi'}</span>{dateLabel && <span>Güncellendi <time dateTime={project.updated_at}>{dateLabel}</time></span>}</div>
    <div className="repository-card-actions"><Link href={`/projeler/${project.id}`}>Projeyi incele <span aria-hidden="true">↗</span></Link>{manage && <ActionLink variant="quiet" href={`/projelerim/${project.id}/duzenle`}>Düzenle</ActionLink>}</div>
  </Surface>;
}
