import {SessionProvider,SessionNavigation} from '../src/components/session-provider';
import type {ReactNode} from 'react';
vi.mock('../src/components/session-provider',async original=>({...await original<typeof import('../src/components/session-provider')>(),GuestOnly:({children}:{children:ReactNode})=>children}));
vi.mock('../src/components/github-auth',()=>({GitHubButton:()=>null}));
vi.mock('../src/components/google-auth',()=>({GoogleButton:()=>null}));
import { render,screen,fireEvent,waitFor } from '@testing-library/react';
import { describe,it,expect,vi } from 'vitest';
import { AuthForm } from '../src/components/auth-form';
import { AccountStatus } from '../src/components/account-status';
const nav=vi.hoisted(()=>({replace:vi.fn(),refresh:vi.fn()}));
vi.mock('next/navigation',()=>({useRouter:()=>nav,usePathname:()=>'/hesap'}));
function login(){fireEvent.change(screen.getByLabelText('E-posta'),{target:{value:'member@example.test'}});fireEvent.change(screen.getByLabelText('Şifre'),{target:{value:'Türkçe42!'}});fireEvent.submit(screen.getByRole('button',{name:'Giriş yap'}).closest('form')!);}
describe('normal auth forms',()=>{
 it('submits login with remember-me and redirects only on success',async()=>{const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({user:{id:1}}));vi.stubGlobal('fetch',fetcher);render(<AuthForm/>);fireEvent.click(screen.getByLabelText('Beni hatırla (30 gün)'));login();await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith('/'));expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({email:'member@example.test',password:'Türkçe42!',remember_me:true});});
 it('disables controls and prevents duplicate submission while pending',async()=>{let resolve!:(response:Response)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(done=>{resolve=done;})));render(<AuthForm/>);login();expect(screen.getByRole('button')).toBeDisabled();fireEvent.submit(screen.getByRole('button').closest('form')!);await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(1));resolve(Response.json({detail:'CSRF reddedildi'},{status:403}));await screen.findByRole('alert');});
 it('shows general and field errors without redirect',async()=>{nav.replace.mockClear();vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({detail:'Alanları kontrol edin.',errors:{email:['Geçersiz e-posta.']}},{status:400})));render(<AuthForm/>);login();expect(await screen.findByRole('alert')).toHaveTextContent('Alanları kontrol edin.');expect(screen.getByLabelText('E-posta')).toHaveAttribute('aria-invalid','true');expect(nav.replace).not.toHaveBeenCalled();expect(screen.getByRole('button')).not.toBeDisabled();});
 it('shows CSRF failure and does not submit credentials',async()=>{const fetcher=vi.fn().mockResolvedValue(Response.json({detail:'Güvenlik doğrulaması başarısız.'},{status:403}));vi.stubGlobal('fetch',fetcher);render(<AuthForm/>);login();expect(await screen.findByRole('alert')).toHaveTextContent('Güvenlik');expect(fetcher).toHaveBeenCalledTimes(1);});
 it('register sends exact backend fields including optional phone',async()=>{const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({user:{id:1}},{status:201}));vi.stubGlobal('fetch',fetcher);render(<AuthForm register/>);for(const [label,value] of [['E-posta','new@example.test'],['Kullanıcı adı','öğrenci'],['Ad soyad','Test Kişi'],['Doğum tarihi','2000-01-02'],['Cinsiyet','unspecified'],['Telefon (isteğe bağlı, doğrulanmaz)','+905551234567'],['Şifre','Türkçe42!']])fireEvent.change(screen.getByLabelText(label),{target:{value}});fireEvent.submit(screen.getByRole('button',{name:'Hesap oluştur'}).closest('form')!);await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({email:'new@example.test',username:'öğrenci',full_name:'Test Kişi',birth_date:'2000-01-02',gender:'unspecified',phone:'+905551234567',password:'Türkçe42!'});});
 it('shows anonymous session instead of invented user data',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(Response.json({user:null})));render(<SessionProvider><AccountStatus/></SessionProvider>);expect(screen.getByRole('status')).toHaveTextContent('Hesap bilgileri yükleniyor');expect(await screen.findByRole('link',{name:'Giriş yap'})).toBeInTheDocument();});
 it('shows unverified-email reminder and working account target',async()=>{vi.stubGlobal('fetch',vi.fn((path:string)=>Promise.resolve(Response.json(path.endsWith('/sessions/')?{sessions:[]}:{user:{id:1,full_name:'Üye',email:'user@example.test',username:'user',email_verified:false,providers:[],has_usable_password:true}}))));render(<SessionProvider><AccountStatus/></SessionProvider>);expect(await screen.findByText('E-posta adresiniz henüz doğrulanmadı.')).toBeInTheDocument();expect(screen.getByRole('button',{name:'Doğrulama e-postasını yeniden gönder'})).toBeInTheDocument();});
});

describe('E revision regression',()=>{
 it('accepts 60 raw username code points that normalize to 30 NFC characters',async()=>{
  const user=(await import('@testing-library/user-event')).default.setup();
  const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({user:{id:1}},{status:201}));vi.stubGlobal('fetch',fetcher);render(<AuthForm register/>);
  const username=screen.getByLabelText('Kullanıcı adı');await user.type(username,'o\u0308'.repeat(30));expect(username).toHaveValue('o\u0308'.repeat(30));expect(username).not.toHaveAttribute('maxlength');expect(username).not.toHaveAttribute('minlength');
  for(const [label,value] of [['E-posta','new@example.test'],['Ad soyad','Test Kişi'],['Doğum tarihi','2000-01-02'],['Cinsiyet','unspecified'],['Şifre','Türkçe42!']])fireEvent.change(screen.getByLabelText(label),{target:{value}});
  await user.click(screen.getByRole('button',{name:'Hesap oluştur'}));await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));expect(JSON.parse(fetcher.mock.calls[1][1].body).username).toBe('ö'.repeat(30));
 });
 it('logs out through CSRF and clears navigation only after success',async()=>{
 const fetcher=vi.fn().mockResolvedValueOnce(Response.json({user:{id:1,full_name:'Üye'}})).mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({detail:'Çıkış'}));vi.stubGlobal('fetch',fetcher);render(<SessionProvider><SessionNavigation/></SessionProvider>);
 fireEvent.click(await screen.findByRole('button',{name:'Çıkış yap'}));expect(await screen.findByRole('link',{name:'Giriş yap'})).toBeInTheDocument();expect(fetcher.mock.calls.map(call=>call[0])).toEqual(['me','csrf','logout'].map(path=>`https://api.first.test/api/auth/${path}/`));
 });
 it('keeps session navigation after logout failure',async()=>{
 const fetcher=vi.fn().mockResolvedValueOnce(Response.json({user:{id:1,full_name:'Üye'}})).mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({detail:'Hizmet kullanılamıyor'},{status:503}));vi.stubGlobal('fetch',fetcher);render(<SessionProvider><SessionNavigation/></SessionProvider>);
 fireEvent.click(await screen.findByRole('button',{name:'Çıkış yap'}));expect(await screen.findByRole('alert')).toHaveTextContent('Hizmet kullanılamıyor');expect(screen.getByRole('button',{name:'Çıkış yap'})).toBeEnabled();expect(screen.getByRole('link',{name:'Hesabım'})).toHaveAttribute('href','/hesap');
 });
 it('blocks duplicate logout while pending',async()=>{
 let resolve!:(response:Response)=>void;const fetcher=vi.fn().mockResolvedValueOnce(Response.json({user:{id:1,full_name:'Üye'}})).mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockImplementationOnce(()=>new Promise<Response>(done=>{resolve=done;}));vi.stubGlobal('fetch',fetcher);render(<SessionProvider><SessionNavigation/></SessionProvider>);
 const button=await screen.findByRole('button',{name:'Çıkış yap'});fireEvent.click(button);fireEvent.click(button);await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(3));expect(button).toBeDisabled();resolve(Response.json({detail:'Çıkış'}));await screen.findByRole('link',{name:'Giriş yap'});expect(fetcher).toHaveBeenCalledTimes(3);
 });
});
