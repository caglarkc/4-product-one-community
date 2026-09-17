import { createHmac } from 'node:crypto';
import { isIP } from 'node:net';
// Imported only by the route handler; BACKEND_URL is never shipped to the browser.
export async function proxyAuth(request:Request, path:string[]):Promise<Response>{
  const reply=(status:number,detail:string)=>Response.json({detail},{status,headers:{'Cache-Control':'no-store'}});
  if(!path.length || path.some(part=>!/^[-a-zA-Z0-9]+$/.test(part))) return reply(404,'Adres bulunamadı.');
  try {
    const base=new URL(process.env.BACKEND_URL || '');
    if(!['https:','http:'].includes(base.protocol)||base.username||base.password||base.pathname!=='/'||base.search||base.hash) throw new Error('Invalid backend origin');
    const headers=new Headers();
    for(const name of ['cookie','content-type','x-csrftoken','origin','referer']){
      const value=request.headers.get(name);if(value) headers.set(name,value);
    }
    headers.set('accept','application/json');
    const secret=process.env.AUTH_PROXY_SECRET || '';
    const ipHeader=process.env.AUTH_CLIENT_IP_HEADER || '';
    if(secret || ipHeader){
      if(secret.length<32 || !/^[!#$%&'*+.^_`|~0-9a-z-]+$/i.test(ipHeader)) throw new Error('Invalid trusted ingress configuration');
      const ip=request.headers.get(ipHeader);
      if(!ip || !isIP(ip) || ip.includes('%')) throw new Error('Missing or invalid ingress IP');
      const timestamp=String(Math.floor(Date.now()/1000));
      const message=`${ip}\n${timestamp}\n${request.method}\n/api/auth/${path.join('/')}/`;
      headers.set('X-First-Client-IP',ip);
      headers.set('X-First-Client-Time',timestamp);
      headers.set('X-First-Client-Signature',createHmac('sha256',secret).update(message).digest('hex'));
    }
    const response=await fetch(new URL(`/api/auth/${path.join('/')}/`,base),{
      method:request.method,headers,cache:'no-store',redirect:'manual',
      body:['GET','HEAD'].includes(request.method)?undefined:await request.text(),
      signal:AbortSignal.timeout(15000),
    });
    // Auth endpoints never redirect. Do not follow or expose a backend redirect.
    if(response.status>=300 && response.status<400) return reply(502,'Kimlik hizmetinden geçersiz yönlendirme alındı.');
    const outgoing=new Headers({'Cache-Control':'no-store','Content-Type':'application/json'});
    for(const cookie of response.headers.getSetCookie()) outgoing.append('Set-Cookie',cookie);
    return new Response(await response.arrayBuffer(),{status:response.status,headers:outgoing});
  }catch{return reply(503,'Kimlik hizmetine ulaşılamadı. Lütfen tekrar deneyin.');}
}
