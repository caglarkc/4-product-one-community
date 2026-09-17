// @vitest-environment node
import { afterEach,describe,it,expect,vi } from 'vitest';
import { proxyAuth } from '../src/lib/backend-proxy';
import config from '../next.config';
afterEach(()=>vi.unstubAllEnvs());
describe('fixed-origin auth proxy',()=>{
 it('keeps API trailing slashes',()=>expect(config.skipTrailingSlashRedirect).toBe(true));
 it('forwards credentials and CSRF, preserves both cookies, never trusts Host',async()=>{
  vi.stubEnv('BACKEND_URL','https://backend.example');
  const headers=new Headers();headers.append('Set-Cookie','sessionid=opaque; HttpOnly; Secure');headers.append('Set-Cookie','csrftoken=csrf; Secure');
  const fetcher=vi.fn().mockResolvedValue(new Response('{"user":null}',{headers}));vi.stubGlobal('fetch',fetcher);
  const response=await proxyAuth(new Request('https://front.example/api/auth/login/',{method:'POST',headers:{Host:'attacker.invalid',Cookie:'csrftoken=old','X-CSRFToken':'csrf',Origin:'https://front.example',Referer:'https://front.example/giris','Content-Type':'application/json'},body:'{}'}),['login']);
  expect(String(fetcher.mock.calls[0][0])).toBe('https://backend.example/api/auth/login/');
  const options=fetcher.mock.calls[0][1];expect(options).toMatchObject({cache:'no-store',redirect:'manual',body:'{}'});expect(options.headers.get('host')).toBeNull();expect(options.headers.get('origin')).toBe('https://front.example');expect(options.headers.get('x-csrftoken')).toBe('csrf');expect(options.headers.get('cookie')).toBe('csrftoken=old');
  expect(response.headers.getSetCookie()).toHaveLength(2);expect(response.headers.get('cache-control')).toBe('no-store');
 });
 it.each(['','https://x.invalid/path','https://u:p@x.invalid','file:///etc/passwd'])('fails closed for invalid configuration %s',async url=>{vi.stubEnv('BACKEND_URL',url);const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);expect((await proxyAuth(new Request('https://front.example/api/auth/me/'),['me'])).status).toBe(503);expect(fetcher).not.toHaveBeenCalled();});
 it('rejects path traversal',async()=>{expect((await proxyAuth(new Request('https://front.example'),['..','secret'])).status).toBe(404);});
 it('does not follow upstream redirects',async()=>{vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(null,{status:302,headers:{Location:'https://other.example'}})));expect((await proxyAuth(new Request('https://front.example'),['me'])).status).toBe(502);});
});

describe('trusted ingress IP assertions',()=>{
 const secret='test-only-shared-key-32-characters-long';
 const request=(ip?:string)=>new Request('https://frontend.example/api/auth/login/',{method:'POST',body:'{}',headers:{...(ip?{'x-trusted-client-ip':ip}:{}),'X-First-Client-IP':'attacker','X-First-Client-Time':'1','X-First-Client-Signature':'spoof'}});
 it('signs validated IP with timestamp, method and exact backend path',async()=>{
  const {createHmac}=await import('node:crypto');vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET',secret);vi.stubEnv('AUTH_CLIENT_IP_HEADER','x-trusted-client-ip');vi.spyOn(Date,'now').mockReturnValue(1800000000000);
  const fetcher=vi.fn().mockResolvedValue(Response.json({user:null}));vi.stubGlobal('fetch',fetcher);expect((await proxyAuth(request('2001:db8::1'),['login'])).status).toBe(200);
  const headers=fetcher.mock.calls[0][1].headers;expect(headers.get('X-First-Client-IP')).toBe('2001:db8::1');expect(headers.get('X-First-Client-Time')).toBe('1800000000');expect(headers.get('X-First-Client-Signature')).toBe(createHmac('sha256',secret).update('2001:db8::1\n1800000000\nPOST\n/api/auth/login/').digest('hex'));expect(headers.has('x-trusted-client-ip')).toBe(false);
 });
 it.each([undefined,'bad','127.0.0.1, 192.0.2.1','127.0.0.1:80','fe80::1%en0'])('rejects absent or invalid single IP %s',async ip=>{
  vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET',secret);vi.stubEnv('AUTH_CLIENT_IP_HEADER','x-trusted-client-ip');const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);expect((await proxyAuth(request(ip),['login'])).status).toBe(503);expect(fetcher).not.toHaveBeenCalled();
 });
 it.each([[secret,''],['','x-trusted-client-ip'],['short','x-trusted-client-ip'],[secret,'invalid header']])('fails closed for secret/header configuration',async(key,header)=>{
  vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET',key);vi.stubEnv('AUTH_CLIENT_IP_HEADER',header);const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);expect((await proxyAuth(request('192.0.2.1'),['login'])).status).toBe(503);expect(fetcher).not.toHaveBeenCalled();
 });
 it('ignores all incoming assertions when signed mode is disabled',async()=>{
  vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET','');vi.stubEnv('AUTH_CLIENT_IP_HEADER','');const fetcher=vi.fn().mockResolvedValue(Response.json({user:null}));vi.stubGlobal('fetch',fetcher);await proxyAuth(request('192.0.2.1'),['login']);const headers=fetcher.mock.calls[0][1].headers;for(const name of ['X-First-Client-IP','X-First-Client-Time','X-First-Client-Signature'])expect(headers.has(name)).toBe(false);
 });
});
