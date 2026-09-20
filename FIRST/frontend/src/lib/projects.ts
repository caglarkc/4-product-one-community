export type ProjectSummary = {id:string;title:string;category:string;subcategory?:string;stage?:string;category_label?:string;subcategory_label?:string;stage_label?:string;description:string;created_at:string;updated_at:string;need_type?:string;participation_mode?:string;need_type_label?:string;participation_mode_label?:string};
export type Project = ProjectSummary & {readme_excerpt:string;is_private:boolean;repository_url:string|null;repository_name:string|null;is_active:boolean;visibility:string;applications_open:boolean;current_state:string;desired_outcome:string;issue_number:number|null;issue_status:string;is_owner:boolean;can_apply:boolean;owner_username:string};
export type ProjectPage = {projects:ProjectSummary[];count:number;next_page:number|null;previous_page:number|null};
export type Repository = {id:number;installation_id:number;full_name:string;name:string;private:boolean;description:string;html_url:string};
export type RepositoryCache = {repositories:Repository[];cached_at:string|null};
export type ProjectPreview = {repository:Repository;readme_excerpt:string;preview_token:string};
export function repositoryCacheCaption(cachedAt:string|null):string {
  if(!cachedAt) return 'Repo listesi henüz kaydedilmedi';
  const date=new Date(cachedAt);
  return Number.isNaN(date.getTime()) ? 'FIRST’te kayıtlı repo listesi' : `FIRST’te kayıtlı liste · Son alım: ${date.toLocaleString('tr-TR')}`;
}
export type TaxonomyOption = {value:string;label:string};
// Optional additions allow the frontend to handle the previous API during rollout.
export type ProjectConfig = {categories:(TaxonomyOption & {subcategories?:TaxonomyOption[]})[];stages?:(TaxonomyOption & {description:string})[];github_app_enabled:boolean;need_types:TaxonomyOption[];participation_modes:TaxonomyOption[];visibilities:TaxonomyOption[]};
export type GitHubStatus = {enabled:boolean;connected:boolean;github_linked:boolean;installation_url:string|null};
export function githubUrl(value:string|null, installation=false):string|null {
  try {const url=new URL(value || '');
    if(url.origin!=='https://github.com'||url.username||url.password||url.hash) return null;
    if(installation ? !/^\/apps\/[a-zA-Z0-9-]+\/installations\/new$/.test(url.pathname) : !/^\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/.test(url.pathname)) return null;
    return url.href;
  }catch{return null;}
}

export type Participation = {id:string;project_id:string;project_title:string;username:string;kind:string;explanation:string;status:string;pr_number:number|null;pr_sha:string;decision:string;github_status:string;github_invitation_url:string;operation_state:string;operation_error:string;merged:boolean};
export type Collaboration = {repository_url:string;pull_requests:{number:number;title:string;url:string;sha:string;draft:boolean}[];issue:{number:number;title:string;url:string;state:string}|null};
export function githubResourceUrl(value:string|null):string|null {
 try {const url=new URL(value || '');if(url.origin!=='https://github.com'||url.username||url.password||url.hash||url.search||!/^\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+(?:\/(?:invitations|(?:pull|issues)\/[1-9][0-9]*))?\/?$/.test(url.pathname))return null;return url.href;}catch{return null;}
}
export const participationStatus:Record<string,string>={pending:'Değerlendirme bekliyor',invited:'FIRST daveti gönderildi',accepted:'Kabul edildi',rejected:'Reddedildi',withdrawn:'Geri çekildi',declined:'Davet reddedildi'};
export const githubStatus:Record<string,string>={invited:'GitHub daveti kabul bekliyor',active:'GitHub erişimi aktif',missing:'GitHub erişimi / daveti bulunamadı'};

export type RepositoryIssues = {issues:{number:number;title:string}[];limit:50};
