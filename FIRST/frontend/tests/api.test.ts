import { describe,it,expect,vi } from 'vitest';
import { api, ApiError } from '../src/lib/api';
describe('auth API transport',()=>{
 it('fetches fresh CSRF for every mutation and sends cookies/no-store',async()=>{
  const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({user:{}})).mockResolvedValueOnce(Response.json({csrfToken:'b'})).mockResolvedValueOnce(Response.json({detail:'ok'}));vi.stubGlobal('fetch',fetcher);
  await api('login',{remember_me:true});await api('logout',{});
  expect(fetcher.mock.calls.map(call=>call[0])).toEqual(['/api/auth/csrf/','/api/auth/login/','/api/auth/csrf/','/api/auth/logout/']);
  expect(fetcher.mock.calls[1][1]).toMatchObject({credentials:'same-origin',cache:'no-store',headers:{'X-CSRFToken':'a'},body:'{"remember_me":true}'});
  expect(fetcher.mock.calls[3][1].headers['X-CSRFToken']).toBe('b');
 });
 it('does not submit when CSRF fails',async()=>{const fetcher=vi.fn().mockResolvedValue(Response.json({detail:'CSRF hata'},{status:403}));vi.stubGlobal('fetch',fetcher);await expect(api('login',{})).rejects.toMatchObject({status:403});expect(fetcher).toHaveBeenCalledTimes(1);});
 it('retains field errors and response codes',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({detail:'Alanlar',errors:{email:['Kullanılıyor']}},{status:400})));await expect(api('register',{})).rejects.toMatchObject({errors:{email:['Kullanılıyor']},status:400});});
 it('uses GET for session and returns anonymous state',async()=>{const fetcher=vi.fn().mockResolvedValue(Response.json({user:null}));vi.stubGlobal('fetch',fetcher);expect(await api('me')).toEqual({user:null});expect(fetcher).toHaveBeenCalledWith('/api/auth/me/',{credentials:'same-origin',cache:'no-store'});});
 it('reports network failure without success',async()=>{vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('private server detail')));await expect(api('me')).rejects.toBeInstanceOf(ApiError);});
});
