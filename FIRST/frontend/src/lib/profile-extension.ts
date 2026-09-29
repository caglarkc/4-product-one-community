export const profileExtensionPath = 'community/extension';
export type StudentStatus = {verified:boolean;verified_at:string|null;expires_at:string|null;email?:string};
export type ContributionCounts = {merged_prs:number;commits:number;projects:number;roles:Record<string,number>};
export type ContributionStats = {since:string;updated_at:string|null;public:ContributionCounts;private?:ContributionCounts;share_private_stats?:boolean;partial?:boolean;scope?:string};
export type PortfolioItem = {id:string;repository_id:number;repository_name:string;repository_url:string;title:string;description:string;role:'owner'|'contributor';created_at:string};
export type Certificate = {id:string;title:string;filename:string;size:number;kind:'pdf'|'image';created_at:string;self_declared:true};
export type CertificatePreview = Certificate & {content:{kind:'pdf'|'image';images:{data_url:string;width:number;height:number}[];truncated:boolean;total_pages?:number}};
export type ProfileExtension = {portfolio:PortfolioItem[];certificates:Certificate[];stats:ContributionStats|null;student:StudentStatus};
export const contributionRoles:Record<string,string>={owner:'Proje sahibi',contributor:'Katkıcı',teammate:'Ekip arkadaşı'};
export function dateLabel(value:string|null|undefined){return value?new Date(value).toLocaleDateString('tr-TR'):'Henüz güncellenmedi';}
export function fileSize(bytes:number){return bytes<1048576?`${Math.ceil(bytes/1024)} KB`:`${(bytes/1048576).toFixed(1)} MB`;}
