// @vitest-environment node
import {afterEach, describe, expect, it, vi} from 'vitest';
import {GET} from '../src/app/accounts/google/login/callback/route';
afterEach(()=>vi.unstubAllEnvs());
describe('Google callback boundary',()=>{
 it.each([['authenticated','/'],['profile_required','/kayit/google'],['reauthenticated','/hesap'],['unknown','/giris?google_error=failed']])('maps %s to fixed destination and retains cookies',async(status,destination)=>{
 vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET','');vi.stubEnv('AUTH_CLIENT_IP_HEADER','');
 const headers=new Headers();headers.append('Set-Cookie','sessionid=next; HttpOnly');headers.append('Set-Cookie','csrftoken=new');
 const fetcher=vi.fn().mockResolvedValue(Response.json({status},{headers}));vi.stubGlobal('fetch',fetcher);
 const result=await GET(new Request('https://front.example/accounts/google/login/callback/?code=secret&state=one&next=https://evil.example&scope=email',{headers:{cookie:'sessionid=before'}}));
 expect(result.status).toBe(303);expect(result.headers.get('location')).toBe(destination);expect(result.headers.getSetCookie()).toHaveLength(2);expect(result.headers.get('referrer-policy')).toBe('no-referrer');
 expect(String(fetcher.mock.calls[0][0])).toBe('https://backend.example/api/auth/google/callback/?code=secret&state=one');expect(fetcher.mock.calls[0][1].headers.get('cookie')).toBe('sessionid=before');
 });
 it('rejects duplicate state before contacting backend',async()=>{
 vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET','');vi.stubEnv('AUTH_CLIENT_IP_HEADER','');const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);
 expect((await GET(new Request('https://front.example/accounts/google/login/callback/?state=a&state=b'))).headers.get('location')).toBe('/giris?google_error=failed');expect(fetcher).not.toHaveBeenCalled();
 });
});

it('signs exact backend callback path while forwarding encoded query separately',async()=>{
 const {createHmac}=await import('node:crypto');const secret='test-only-shared-key-32-characters-long';
 vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET',secret);vi.stubEnv('AUTH_CLIENT_IP_HEADER','x-trusted-client-ip');vi.spyOn(Date,'now').mockReturnValue(1800000000000);
 const fetcher=vi.fn().mockResolvedValue(Response.json({status:'authenticated'}));vi.stubGlobal('fetch',fetcher);
 await GET(new Request('https://front.example/accounts/google/login/callback/?code=a%2Bb&state=c',{headers:{'x-trusted-client-ip':'192.0.2.1'}}));
 expect(fetcher.mock.calls[0][1].headers.get('X-First-Client-Signature')).toBe(createHmac('sha256',secret).update('192.0.2.1\n1800000000\nGET\n/api/auth/google/callback/').digest('hex'));
 expect(new URL(fetcher.mock.calls[0][0]).searchParams.get('code')).toBe('a+b');
});
it('turns cancellation into a fixed safe error route',async()=>{
 vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET','');vi.stubEnv('AUTH_CLIENT_IP_HEADER','');vi.stubGlobal('fetch',vi.fn().mockResolvedValue(Response.json({detail:'raw token or provider details'},{status:400})));
 const result=await GET(new Request('https://front.example/accounts/google/login/callback/?error=access_denied&state=one'));
 expect(result.headers.get('location')).toBe('/giris?google_error=cancelled');
});
