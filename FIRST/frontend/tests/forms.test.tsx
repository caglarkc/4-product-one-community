import { render,screen,fireEvent,waitFor } from '@testing-library/react';
import { describe,it,expect,vi } from 'vitest';
import { AuthForm } from '../src/components/auth-form';
import { AccountStatus } from '../src/components/account-status';
const nav=vi.hoisted(()=>({replace:vi.fn(),refresh:vi.fn()}));
vi.mock('next/navigation',()=>({useRouter:()=>nav}));
function login(){fireEvent.change(screen.getByLabelText('E-posta'),{target:{value:'member@example.test'}});fireEvent.change(screen.getByLabelText('Şifre'),{target:{value:'Türkçe42!'}});fireEvent.submit(screen.getByRole('button',{name:'Giriş yap'}).closest('form')!);}
describe('normal auth forms',()=>{
 it('submits login with remember-me and redirects only on success',async()=>{const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({user:{id:1}}));vi.stubGlobal('fetch',fetcher);render(<AuthForm/>);fireEvent.click(screen.getByLabelText('Beni hatırla (30 gün)'));login();await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith('/hesap'));expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({email:'member@example.test',password:'Türkçe42!',remember_me:true});});
 it('disables controls and prevents duplicate submission while pending',async()=>{vi.stubGlobal('fetch',vi.fn(()=>new Promise(()=>{})));render(<AuthForm/>);login();expect(screen.getByRole('button')).toBeDisabled();fireEvent.submit(screen.getByRole('button').closest('form')!);expect(fetch).toHaveBeenCalledTimes(1);expect(screen.getByRole('button')).toHaveTextContent('İşlem sürüyor');});
 it('shows general and field errors without redirect',async()=>{nav.replace.mockClear();vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({detail:'Alanları kontrol edin.',errors:{email:['Geçersiz e-posta.']}},{status:400})));render(<AuthForm/>);login();expect(await screen.findByRole('alert')).toHaveTextContent('Alanları kontrol edin.');expect(screen.getByLabelText('E-posta')).toHaveAttribute('aria-invalid','true');expect(nav.replace).not.toHaveBeenCalled();expect(screen.getByRole('button')).not.toBeDisabled();});
 it('shows CSRF failure and does not submit credentials',async()=>{const fetcher=vi.fn().mockResolvedValue(Response.json({detail:'Güvenlik doğrulaması başarısız.'},{status:403}));vi.stubGlobal('fetch',fetcher);render(<AuthForm/>);login();expect(await screen.findByRole('alert')).toHaveTextContent('Güvenlik');expect(fetcher).toHaveBeenCalledTimes(1);});
 it('register sends exact backend fields including optional phone',async()=>{const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({user:{id:1}},{status:201}));vi.stubGlobal('fetch',fetcher);render(<AuthForm register/>);for(const [label,value] of [['E-posta','new@example.test'],['Kullanıcı adı','öğrenci'],['Ad soyad','Test Kişi'],['Doğum tarihi','2000-01-02'],['Cinsiyet','unspecified'],['Telefon (isteğe bağlı, doğrulanmaz)','+905551234567'],['Şifre','Türkçe42!']])fireEvent.change(screen.getByLabelText(label),{target:{value}});fireEvent.submit(screen.getByRole('button',{name:'Kayıt ol'}).closest('form')!);await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({email:'new@example.test',username:'öğrenci',full_name:'Test Kişi',birth_date:'2000-01-02',gender:'unspecified',phone:'+905551234567',password:'Türkçe42!'});});
 it('shows anonymous session instead of invented user data',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(Response.json({user:null})));render(<AccountStatus/>);expect(screen.getByRole('status')).toHaveTextContent('Oturum kontrol');expect(await screen.findByText(/Oturumunuz açık değil/)).toBeInTheDocument();});
 it('shows unverified-email reminder and honest temporary target',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(Response.json({user:{full_name:'Üye',email_verified:false}})));render(<AccountStatus/>);expect(await screen.findByText('E-posta adresiniz henüz doğrulanmadı.')).toBeInTheDocument();expect(screen.getByText(/sonraki uygulama aşamasında/)).toBeInTheDocument();});
});

describe('E revision regression',()=>{
 it('accepts 60 raw username code points that normalize to 30 NFC characters',async()=>{
  const user=(await import('@testing-library/user-event')).default.setup();
  const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({user:{id:1}},{status:201}));vi.stubGlobal('fetch',fetcher);render(<AuthForm register/>);
  const username=screen.getByLabelText('Kullanıcı adı');await user.type(username,'o\u0308'.repeat(30));expect(username).toHaveValue('o\u0308'.repeat(30));expect(username).not.toHaveAttribute('maxlength');expect(username).not.toHaveAttribute('minlength');
  for(const [label,value] of [['E-posta','new@example.test'],['Ad soyad','Test Kişi'],['Doğum tarihi','2000-01-02'],['Cinsiyet','unspecified'],['Şifre','Türkçe42!']])fireEvent.change(screen.getByLabelText(label),{target:{value}});
  await user.click(screen.getByRole('button',{name:'Kayıt ol'}));await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));expect(JSON.parse(fetcher.mock.calls[1][1].body).username).toBe('ö'.repeat(30));
 });
 it('logs out through CSRF and navigates only after successful response',async()=>{
  nav.replace.mockClear();const fetcher=vi.fn().mockResolvedValueOnce(Response.json({user:{full_name:'Üye'}})).mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({detail:'Çıkış'}));vi.stubGlobal('fetch',fetcher);render(<AccountStatus/>);
  fireEvent.click(await screen.findByRole('button',{name:'Çıkış yap'}));await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith('/giris'));expect(fetcher.mock.calls.map(call=>call[0])).toEqual(['/api/auth/me/','/api/auth/csrf/','/api/auth/logout/']);expect(screen.getByText(/Oturumunuz açık değil/)).toBeInTheDocument();
 });
 it('keeps session visible and offers retry after logout error',async()=>{
  nav.replace.mockClear();const fetcher=vi.fn().mockResolvedValueOnce(Response.json({user:{full_name:'Üye'}})).mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockResolvedValueOnce(Response.json({detail:'Hizmet kullanılamıyor'},{status:503}));vi.stubGlobal('fetch',fetcher);render(<AccountStatus/>);
  fireEvent.click(await screen.findByRole('button',{name:'Çıkış yap'}));expect(await screen.findByRole('alert')).toHaveTextContent('Hizmet kullanılamıyor');expect(screen.getByText('Merhaba, Üye.')).toBeInTheDocument();expect(screen.getByRole('button',{name:'Çıkış yap'})).not.toBeDisabled();expect(nav.replace).not.toHaveBeenCalled();
 });
 it('blocks double logout while mutation is pending',async()=>{
  let resolve!:(response:Response)=>void;
  const fetcher=vi.fn().mockResolvedValueOnce(Response.json({user:{full_name:'Üye'}})).mockResolvedValueOnce(Response.json({csrfToken:'a'})).mockImplementationOnce(()=>new Promise<Response>(done=>{resolve=done;}));vi.stubGlobal('fetch',fetcher);render(<AccountStatus/>);
  const button=await screen.findByRole('button',{name:'Çıkış yap'});fireEvent.click(button);fireEvent.click(button);await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(3));expect(button).toBeDisabled();expect(button).toHaveTextContent('Çıkış yapılıyor');resolve(Response.json({detail:'Çıkış'}));await screen.findByText(/Oturumunuz açık değil/);expect(fetcher).toHaveBeenCalledTimes(3);
 });
});
