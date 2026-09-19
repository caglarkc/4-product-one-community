export type ConnectedAccount = {provider: 'google' | 'github'; display_name: string; username: string; email: string; avatar_url: string; profile_url: string};
export type User = {id:number;email:string;username:string;full_name:string;birth_date:string|null;gender:string;phone:string;email_verified:boolean;phone_verified:boolean;profile_complete:boolean;providers:string[];connected_accounts?:ConnectedAccount[];has_usable_password?:boolean;capabilities:{can_apply:boolean;can_create_listing:boolean}};
export class ApiError extends Error {
  constructor(message:string, public status:number, public errors:Record<string,string[]> = {}, public code?:string, public redirectTo?:string){super(message);}
}
const sessionKey = 'first.api.session';
const keyPattern = /^[a-z0-9]{32}$/;
let queue:Promise<unknown> = Promise.resolve();
function serialized<T>(work:()=>Promise<T>):Promise<T> {
  const next = queue.then(work, work); queue = next.catch(()=>undefined); return next;
}
function token():string|null {
  const value = localStorage.getItem(sessionKey);
  return value && keyPattern.test(value) ? value : null;
}
function origin():string {
  const url = new URL(process.env.NEXT_PUBLIC_API_URL || '');
  if(url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error('Invalid API origin');
  return url.origin;
}
async function request<T>(path:string, options:RequestInit = {}, query?:URLSearchParams):Promise<T> {
  if(!/^[a-z0-9-]+(?:\/[a-z0-9-]+)*$/.test(path)) throw new ApiError('Geçersiz API adresi.',400);
  const sent = token();
  const headers = new Headers(options.headers);
  if(sent) headers.set('Authorization', `Bearer ${sent}`);
  const response = await fetch(`${origin()}/api/auth/${path}/${query?.size ? `?${query}` : ''}`, {
    ...options, headers, credentials:'omit', cache:'no-store', redirect:'error', signal:AbortSignal.timeout(30000),
  });
  const updated = response.headers.get('X-First-Session');
  // An old response must never replace a newer login from this or another tab.
  if(updated !== null && token() === sent) {
    if(updated === '') localStorage.removeItem(sessionKey);
    else if(keyPattern.test(updated)) localStorage.setItem(sessionKey, updated);
    else throw new ApiError('Geçersiz oturum yanıtı.',502);
  }
  const body = await response.json().catch(()=>null);
  if(!response.ok) throw new ApiError(body?.detail || 'İşlem tamamlanamadı. Lütfen tekrar deneyin.',response.status,body?.errors,body?.code,body?.redirect_to);
  if(!body) throw new ApiError('Sunucudan geçersiz yanıt alındı.',502);
  return body as T;
}
async function csrf():Promise<string> {
  let result:{csrfToken:string};
  try {result = await request('csrf');}
  catch(error) {
    if(!(error instanceof ApiError) || error.code !== 'invalid_session') throw error;
    result = await request('csrf');
  }
  if(!result.csrfToken) throw new ApiError('Güvenlik doğrulaması alınamadı.',403);
  return result.csrfToken;
}
async function boundary<T>(work:()=>Promise<T>):Promise<T> {
  try {return await work();}
  catch(error) {
    if(error instanceof ApiError) throw error;
    throw new ApiError('Sunucuya ulaşılamadı. Bağlantınızı kontrol edip tekrar deneyin.',503);
  }
}
export function api<T>(path:string, body?:unknown, method='POST'):Promise<T> {
  return boundary(()=>serialized(async()=> {
    if(body === undefined) return request<T>(path);
    const csrfToken = await csrf();
    return request<T>(path,{method,headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken},body:JSON.stringify(body)});
  }));
}
export function oauthCallback(path:string, query:URLSearchParams):Promise<{redirect_to:string}> {
  return boundary(()=>serialized(()=>request<{redirect_to:string}>(path,{},query)));
}
export function oauthDestination(value:unknown):string {
  const fixed = ['/', '/hesap', '/kayit/google', '/kayit/github', '/github-kurulum?next=%2F', '/github-kurulum?next=%2Fhesap', '/github-kurulum?github=failed'];
  for(const provider of ['google','github']) for(const error of ['failed','cancelled']) fixed.push(`/giris?${provider}_error=${error}`);
  for(const next of ['/','/hesap','/projelerim/yeni']) fixed.push(`/github-kurulum?github=connected&next=${encodeURIComponent(next)}`);
  if(typeof value !== 'string' || !fixed.includes(value)) throw new ApiError('Geçersiz yönlendirme yanıtı.',502);
  return value;
}
