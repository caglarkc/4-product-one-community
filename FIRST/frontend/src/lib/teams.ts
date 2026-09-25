import type {PageInfo} from './community';
import type {ProjectSummary} from './projects';
export type TeamRole='owner'|'admin'|'member';
export type Team={id:string;name:string;description:string;recruiting:boolean;recruitment_text:string;skills:string[];organization_url:string;owner_username:string;my_role:TeamRole|null;is_active:boolean;saved:boolean;created_at:string;updated_at:string};
export type TeamDraft=Pick<Team,'name'|'description'|'recruiting'|'recruitment_text'|'skills'|'organization_url'>;
export type TeamRequest={id:string;team_id:string;team_name:string;username:string;kind:'application'|'invitation';status:'pending'|'accepted'|'rejected'|'withdrawn'|'declined';explanation:string;created_at:string};
export type TeamMember={username:string;full_name:string;role:TeamRole};
export type TeamDetail={team:Team;members:TeamMember[];projects:ProjectSummary[];requests:TeamRequest[];my_request:TeamRequest|null;member_pagination:PageInfo;request_pagination:PageInfo;project_pagination:PageInfo};
export type TeamPage=PageInfo&{teams:Team[]};
export type TeamMine={teams:Team[];invitations:TeamRequest[];team_pagination:PageInfo;invitation_pagination:PageInfo};
export const teamRoles:Record<TeamRole,string>={owner:'Sahip',admin:'Yönetici',member:'Üye'};
export const teamRequestStatus:Record<TeamRequest['status'],string>={pending:'Bekliyor',accepted:'Kabul edildi',rejected:'Reddedildi',withdrawn:'Geri çekildi',declined:'Davet reddedildi'};
export function organizationHref(value:string){try{const url=new URL(value);return url.origin==='https://github.com'&&!url.username&&!url.password&&!url.search&&!url.hash&&/^\/[a-zA-Z0-9-]+$/.test(url.pathname)?url.href:null;}catch{return null;}}
