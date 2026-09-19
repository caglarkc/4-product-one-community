// @vitest-environment node
import {afterEach,expect,it,vi} from 'vitest';
import {GET} from '../src/app/github-repo/callback/route';
afterEach(()=>vi.unstubAllEnvs());
it.each([['connected','connected'],['unknown','failed']])('forwards only approved App callback fields and fixed %s redirect',async(status,result)=>{
 vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET','');vi.stubEnv('AUTH_CLIENT_IP_HEADER','');
 const fetcher=vi.fn().mockResolvedValue(Response.json({status},{headers:{'Set-Cookie':'sessionid=next; HttpOnly'}}));vi.stubGlobal('fetch',fetcher);
 const response=await GET(new Request('https://front.example/github-repo/callback?code=one&state=two&installation_id=3&next=https://evil.example'));
 expect(response.headers.get('location')).toBe(result === 'connected' ? '/github-kurulum?github=connected&next=%2Fprojelerim%2Fyeni' : '/github-kurulum?github=failed');expect(response.headers.getSetCookie()).toHaveLength(1);expect(String(fetcher.mock.calls[0][0])).toBe('https://backend.example/api/auth/projects/github/callback/?code=one&state=two');
});
it.each([['/hesap','%2Fhesap'], ['https://evil.example','%2Fprojelerim%2Fyeni']])('callback bounds persisted return_to %s', async (return_to, encoded) => {
 vi.stubEnv('BACKEND_URL','https://backend.example');vi.stubEnv('AUTH_PROXY_SECRET','');vi.stubEnv('AUTH_CLIENT_IP_HEADER','');vi.stubGlobal('fetch',vi.fn().mockResolvedValue(Response.json({status:'connected',return_to})));
 const response=await GET(new Request('https://front.example/github-repo/callback?code=one&state=two'));expect(response.headers.get('location')).toBe(`/github-kurulum?github=connected&next=${encoded}`);
});
