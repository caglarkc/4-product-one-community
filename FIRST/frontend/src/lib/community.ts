import type {TaxonomyOption, ProjectSummary} from './projects';
export type PublicProfile={username:string;full_name:string;bio:string;website:string;skills:string[];interests:string[];invitations_open:boolean;github_username:string;github_url:string;avatar_url:string};
export type CommunityConfig={skills:TaxonomyOption[];technologies:TaxonomyOption[];interests:TaxonomyOption[];report_reasons:TaxonomyOption[]};
export type PageInfo={count:number;next_page:number|null;previous_page:number|null};
export type ProfilePage=PageInfo & {profile:PublicProfile;projects:ProjectSummary[]};
export function profileHref(username:string){return `/kisiler/${encodeURIComponent(username)}`;}
export function safeWebsite(value:string){try{const url=new URL(value);return ['https:','http:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}}
export function labels(values:string[],options:TaxonomyOption[]=[]){return values.map(value=>options.find(item=>item.value===value)?.label||value).join(' · ');}
