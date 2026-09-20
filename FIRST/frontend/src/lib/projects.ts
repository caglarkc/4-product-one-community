export type Project = {id:string;title:string;category:string;subcategory?:string;stage?:string;category_label?:string;subcategory_label?:string;stage_label?:string;description:string;readme_excerpt:string;is_private:boolean;repository_url:string|null;repository_name:string|null;is_active:boolean;created_at:string;updated_at:string};
export type Repository = {id:number;installation_id:number;full_name:string;name:string;private:boolean;description:string;html_url:string};
export type TaxonomyOption = {value:string;label:string};
// Optional additions allow the frontend to handle the previous API during rollout.
export type ProjectConfig = {categories:(TaxonomyOption & {subcategories?:TaxonomyOption[]})[];stages?:(TaxonomyOption & {description:string})[];github_app_enabled:boolean};
export type GitHubStatus = {enabled:boolean;connected:boolean;github_linked:boolean;installation_url:string|null};
export function githubUrl(value:string|null, installation=false):string|null {
  try {const url=new URL(value || '');
    if(url.origin!=='https://github.com'||url.username||url.password||url.hash) return null;
    if(installation ? !/^\/apps\/[a-zA-Z0-9-]+\/installations\/new$/.test(url.pathname) : !/^\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/.test(url.pathname)) return null;
    return url.href;
  }catch{return null;}
}
