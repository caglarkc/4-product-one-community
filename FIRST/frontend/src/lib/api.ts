export type ConnectedAccount = {provider: 'google' | 'github'; display_name: string; username: string; email: string; avatar_url: string; profile_url: string};
export type User = {id:number;email:string;username:string;full_name:string;birth_date:string|null;gender:string;phone:string;email_verified:boolean;phone_verified:boolean;profile_complete:boolean;providers:string[];connected_accounts?:ConnectedAccount[];has_usable_password?:boolean;capabilities:{can_apply:boolean;can_create_listing:boolean}};
export class ApiError extends Error {
  constructor(message:string, public status:number, public errors:Record<string,string[]> = {}, public code?:string, public redirectTo?:string){super(message);}
}
export const sessionKey = 'first.api.session';
export const sessionChangedEvent = 'first:session-changed';
export type SessionChange = {user?: User | null; revalidate?: boolean};
const keyPattern = /^[a-z0-9]{32}$/;
let queue:Promise<unknown> = Promise.resolve();
function serialized<T>(work:()=>Promise<T>):Promise<T> {
  const next = queue.then(work, work); queue = next.catch(()=>undefined); return next;
}
export function sessionToken():string|null {
  const value = localStorage.getItem(sessionKey);
  return value && keyPattern.test(value) ? value : null;
}
function origin():string {
  const url = new URL(process.env.NEXT_PUBLIC_API_URL || '');
  if(url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error('Invalid API origin');
  return url.origin;
}
function sessionChanged():ApiError {return new ApiError('Oturumunuz değişti. Lütfen işlemi yeniden başlatın.',409,{},'session_changed');}
async function request<T>(path:string, options:RequestInit = {}, query?:URLSearchParams, session?:{expected:string|null; accepted?:(token:string|null)=>void}):Promise<T> {
  if(!/^[a-z0-9-]+(?:\/[a-z0-9-]+)*$/.test(path)) throw new ApiError('Geçersiz API adresi.',400);
  const sent = sessionToken();
  if(session && sent !== session.expected) throw sessionChanged();
  const headers = new Headers(options.headers);
  if(sent) headers.set('Authorization', `Bearer ${sent}`);
  const response = await fetch(`${origin()}/api/auth/${path}/${query?.size ? `?${query}` : ''}`, {
    ...options, headers, credentials:'omit', cache:'no-store', redirect:'error', signal:AbortSignal.timeout(30000),
  });
  if(sessionToken() !== sent) throw sessionChanged();
  const updated = response.headers.get('X-First-Session');
  const body = await response.json().catch(()=>null);
  // Parsing a response can yield to a login/logout in another tab as well.
  if(sessionToken() !== sent) throw sessionChanged();
  let changed = false;
  if(updated !== null) {
    if(updated === '') localStorage.removeItem(sessionKey);
    else if(keyPattern.test(updated)) localStorage.setItem(sessionKey, updated);
    else throw new ApiError('Geçersiz oturum yanıtı.',502);
    changed = sessionToken() !== sent;
  }
  if(!response.ok && body?.code === 'invalid_session') {
    localStorage.removeItem(sessionKey);
    window.dispatchEvent(new CustomEvent<SessionChange>(sessionChangedEvent, {detail: {user: null}}));
  } else if(response.ok && path !== 'me' && body && Object.hasOwn(body, 'user')) {
    window.dispatchEvent(new CustomEvent<SessionChange>(sessionChangedEvent, {detail: {user: body.user}}));
  } else if((changed && path !== 'csrf') || (response.ok && options.method && /^(logout|password\/(change|reset)|email\/verify|sessions(?:\/|$)|account$)/.test(path))) {
    // Revoking another device or verifying this email does not replace the
    // current identity. Revalidate without discarding in-progress account forms.
    // A rotated key or any other unknown auth transition still clears private UI.
    const revalidate = !changed && (/^sessions\/(?!revoke$)[a-z0-9-]+$/.test(path) || path === 'email/verify' || path === 'password/reset');
    window.dispatchEvent(new CustomEvent<SessionChange>(sessionChangedEvent, {detail: sessionToken() ? {revalidate} : {user: null}}));
  }
  if(!response.ok) throw new ApiError(body?.detail || 'İşlem tamamlanamadı. Lütfen tekrar deneyin.',response.status,body?.errors,body?.code,body?.redirect_to);
  if(!body) throw new ApiError('Sunucudan geçersiz yanıt alındı.',502);
  session?.accepted?.(updated === null ? sent : updated || null);
  return body as T;
}
async function csrf(expected:string|null):Promise<{csrfToken:string; session:string|null}> {
  let accepted = expected;
  const result = await request<{csrfToken:string}>('csrf',{},undefined,{expected,accepted:value=>{accepted=value;}});
  if(!result.csrfToken) throw new ApiError('Güvenlik doğrulaması alınamadı.',403);
  return {csrfToken:result.csrfToken,session:accepted};
}
async function boundary<T>(work:()=>Promise<T>):Promise<T> {
  try {return await work();}
  catch(error) {
    if(error instanceof ApiError) throw error;
    throw new ApiError('Sunucuya ulaşılamadı. Bağlantınızı kontrol edip tekrar deneyin.',503);
  }
}
export function api<T>(path:string, body?:unknown, method='POST', query?:URLSearchParams):Promise<T> {
  return boundary(()=> {
    const expected = sessionToken();
    return serialized(async()=> {
      if(body === undefined) return request<T>(path,{},query);
      // Bind queued form submissions to their original identity, then bind the
      // mutation to the exact session that issued CSRF (including anonymous bootstrap).
      if(sessionToken() !== expected) throw sessionChanged();
      const proof = await csrf(expected);
      return request<T>(path,{method,headers:{'Content-Type':'application/json','X-CSRFToken':proof.csrfToken},body:JSON.stringify(body)},undefined,{expected:proof.session});
    });
  });
}
/** The public feed never joins the authenticated queue or reads/writes session state. */
export function publicProjectFeed<T>(query:URLSearchParams, signal:AbortSignal):Promise<T> {
  return boundary(async()=> {
    const controller = new AbortController();
    const cancel = () => controller.abort(signal.reason);
    if(signal.aborted) cancel();
    else signal.addEventListener('abort',cancel,{once:true});
    const timeout = setTimeout(()=>controller.abort(new DOMException('Request timed out','TimeoutError')),30000);
    try {
      const response = await fetch(`${origin()}/api/auth/projects/${query.size ? `?${query}` : ''}`, {
        method:'GET', headers:{Accept:'application/json'}, credentials:'omit', cache:'no-store', redirect:'error', signal:controller.signal,
      });
      const body = await response.json().catch(()=>null);
      if(controller.signal.aborted) throw controller.signal.reason;
      if(!response.ok) throw new ApiError(body?.detail || 'Projeler yüklenemedi. Lütfen tekrar deneyin.',response.status,body?.errors,body?.code);
      if(!body) throw new ApiError('Sunucudan geçersiz yanıt alındı.',502);
      return body as T;
    } finally {
      clearTimeout(timeout);
      signal.removeEventListener('abort',cancel);
    }
  });
}
export function oauthCallback(path:string, query:URLSearchParams):Promise<{redirect_to:string}> {
  return boundary(()=> {
    const expected = sessionToken();
    return serialized(()=>request<{redirect_to:string}>(path,{},query,{expected}));
  });
}
export function oauthDestination(value:unknown):string {
  const fixed = ['/', '/hesap', '/kayit/google', '/kayit/github', '/github-kurulum?next=%2F', '/github-kurulum?next=%2Fhesap', '/github-kurulum?github=failed'];
  for(const provider of ['google','github']) for(const error of ['failed','cancelled']) fixed.push(`/giris?${provider}_error=${error}`);
  for(const next of ['/','/hesap','/projelerim/yeni']) fixed.push(`/github-kurulum?github=connected&next=${encodeURIComponent(next)}`);
  if(typeof value !== 'string' || !fixed.includes(value)) throw new ApiError('Geçersiz yönlendirme yanıtı.',502);
  return value;
}
