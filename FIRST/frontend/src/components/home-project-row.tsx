import Link from 'next/link';
import {profileHref} from '../lib/community';
import type {ProjectSummary} from '../lib/projects';

const dateFormatter = new Intl.DateTimeFormat('tr-TR', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'});

export function HomeProjectRow({project}: {project: ProjectSummary}) {
  const date = new Date(project.updated_at);
  const dateLabel = Number.isNaN(date.getTime()) ? null : dateFormatter.format(date);
  const facts = [
    {label:'Kategori', value:project.category_label || 'Kategori belirtilmedi'},
    {label:'Proje aşaması', value:project.stage_label || 'Aşama belirtilmedi'},
    {label:'Alt kategori', value:project.subcategory_label || 'Alt kategori belirtilmedi'},
    {label:'Aranan katkı', value:project.need_type_label || 'Katkı belirtilmedi', accent:true},
    {label:'Katılım yöntemi', value:project.participation_mode_label || 'Katılım belirtilmedi', accent:true},
  ];

  return <article className="home-project-row" aria-labelledby={`project-title-${project.id}`}>
    <div className="home-project-summary">
      <h3 id={`project-title-${project.id}`} className="home-project-title"><Link href={`/projeler/${project.id}`}>{project.title}</Link></h3>
      <p className="home-project-description">{project.description || 'Bu proje için henüz bir açıklama eklenmedi.'}</p>
    </div>
    <dl className="home-project-facts">
      {facts.map(fact => <div key={fact.label} className={`home-project-fact${fact.accent ? ' home-project-fact--accent' : ''}`}>
        <dt className="home-project-fact-label">{fact.label}</dt>
        <dd>{fact.value}</dd>
      </div>)}
    </dl>
    <div className="home-project-meta">
      {project.owner_username && <Link href={profileHref(project.owner_username)}>@{project.owner_username}</Link>}
      {dateLabel && <time dateTime={project.updated_at} title="Son güncelleme">{dateLabel}</time>}
    </div>
  </article>;
}
