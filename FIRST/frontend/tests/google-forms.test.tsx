import type {ReactNode} from 'react';
vi.mock('../src/components/session-provider',async original=>({...await original<typeof import('../src/components/session-provider')>(),GuestOnly:({children}:{children:ReactNode})=>children}));
import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import {GoogleSignup} from '../src/components/google-signup';
import {GoogleButton} from '../src/components/google-auth';
const nav=vi.hoisted(()=>({replace:vi.fn(),refresh:vi.fn()}));
vi.mock('next/navigation',()=>({useRouter:()=>nav}));
const pending={profile:{email:'member@gmail.com',full_name:'Google Üye',username:'',birth_date:'',gender:'',phone:''},email_verified:true,email_editable:false};
describe('Google registration',()=>{
 it('prefills trusted email and sends profile without password or immutable email',async()=>{
 const fetcher=vi.fn().mockResolvedValueOnce(Response.json(pending)).mockResolvedValueOnce(Response.json({csrfToken:'csrf'})).mockResolvedValueOnce(Response.json({user:{id:1},redirect_to:'/'}));vi.stubGlobal('fetch',fetcher);render(<GoogleSignup/>);
 expect(await screen.findByLabelText('E-posta')).toHaveValue('member@gmail.com');expect(screen.getByLabelText('E-posta')).toHaveAttribute('readonly');expect(screen.queryByLabelText('Şifre')).not.toBeInTheDocument();expect(screen.getByLabelText('Ad soyad')).toHaveValue('Google Üye');
 for(const [label,value] of [['Kullanıcı adı','u\u0308ye'],['Doğum tarihi','2000-01-01'],['Cinsiyet','unspecified']]) fireEvent.change(screen.getByLabelText(label),{target:{value}});
 fireEvent.submit(screen.getByRole('button',{name:'Kaydı tamamla'}).closest('form')!);await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith('/'));
 expect(JSON.parse(fetcher.mock.calls[2][1].body)).toEqual({full_name:'Google Üye',username:'üye',birth_date:'2000-01-01',phone:'',gender:'unspecified'});
 });
 it('offers restart for expired pending signup',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(Response.json({detail:'Kayıt süresi doldu.'},{status:400})));render(<GoogleSignup/>);expect(await screen.findByRole('alert')).toHaveTextContent('Kayıt süresi doldu');expect(screen.getByRole('link',{name:'Google ile yeniden giriş yap'})).toHaveAttribute('href','/giris');
 });
 it('rejects non-Google redirect and permits retry',async()=>{
 const fetcher=vi.fn().mockResolvedValueOnce(Response.json({providers:{google:true}})).mockResolvedValueOnce(Response.json({csrfToken:'csrf'})).mockResolvedValueOnce(Response.json({authorization_url:'https://evil.example/'}));vi.stubGlobal('fetch',fetcher);render(<GoogleButton remember/>);
 fireEvent.click(await screen.findByRole('button',{name:'Google ile devam et'}));expect(await screen.findByRole('alert')).toHaveTextContent('doğrulanamadı');expect(JSON.parse(fetcher.mock.calls[2][1].body)).toEqual({remember_me:true,purpose:'login'});expect(screen.getByRole('button')).not.toBeDisabled();
 });
});

it('blocks unverified signup, preserves editable fields and requests proof for corrected email',async()=>{
 const fetcher=vi.fn().mockResolvedValueOnce(Response.json({...pending,email_editable:true,email_verified:false})).mockResolvedValueOnce(Response.json({csrfToken:'csrf'})).mockResolvedValueOnce(Response.json({detail:'Bağlantı gönderildi.'}));vi.stubGlobal('fetch',fetcher);render(<GoogleSignup/>);
 const email=await screen.findByLabelText('E-posta');expect(email).not.toHaveAttribute('readonly');fireEvent.change(email,{target:{value:'corrected@example.test'}});
 fireEvent.change(screen.getByLabelText('Kullanıcı adı'),{target:{value:'member'}});
 const complete=screen.getByRole('button',{name:'Kaydı tamamla'});expect(complete).toBeDisabled();fireEvent.submit(complete.closest('form')!);expect(fetcher).toHaveBeenCalledTimes(1);
 fireEvent.click(screen.getByRole('button',{name:'E-posta doğrulama bağlantısı gönder'}));expect(await screen.findByRole('status')).toHaveTextContent('Bağlantı gönderildi.');expect(JSON.parse(fetcher.mock.calls[2][1].body).email).toBe('corrected@example.test');expect(screen.getByLabelText('Kullanıcı adı')).toHaveValue('member');expect(complete).toBeDisabled();
});

it('offers Google reauthentication for passwordless accounts without asking for a password',async()=>{
 const {AccountForm,ReauthenticationContext}=await import('../src/components/account-form');
 vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'csrf'})).mockResolvedValueOnce(Response.json({detail:'Kimliğinizi doğrulayın.',code:'reauthentication_required'},{status:403})));
 render(<ReauthenticationContext.Provider value={{google:true,password:false}}><AccountForm title="E-posta değiştir" path="email/change" submit="Kaydet"/></ReauthenticationContext.Provider>);
 fireEvent.submit(screen.getByRole('button',{name:'Kaydet'}).closest('form')!);
 expect(await screen.findByRole('button',{name:'Google ile kimliğimi doğrula'})).toBeInTheDocument();expect(screen.queryByLabelText('Mevcut şifreniz')).not.toBeInTheDocument();expect(screen.getByRole('button',{name:'Kaydet'})).toBeDisabled();
});

it('requests mailbox proof without submitting the incomplete profile',async()=>{
 const fetcher=vi.fn().mockResolvedValueOnce(Response.json({...pending,email_editable:true,email_verified:false})).mockResolvedValueOnce(Response.json({csrfToken:'csrf'})).mockResolvedValueOnce(Response.json({detail:'Bağlantı gönderildi.'}));vi.stubGlobal('fetch',fetcher);render(<GoogleSignup/>);
 fireEvent.click(await screen.findByRole('button',{name:'E-posta doğrulama bağlantısı gönder'}));expect(await screen.findByRole('status')).toHaveTextContent('Bağlantı gönderildi.');expect(fetcher.mock.calls[2][0]).toBe('https://api.first.test/api/auth/google/email/request/');expect(JSON.parse(fetcher.mock.calls[2][1].body)).toEqual({email:'member@gmail.com'});
});
it('does not verify email on opening the page; explicit confirmation posts key and routes known status',async()=>{
 const {VerifyGoogleEmail}=await import('../src/components/google-email');
 const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'csrf'})).mockResolvedValueOnce(Response.json({status:'profile_required',redirect_to:'/kayit/google'}));vi.stubGlobal('fetch',fetcher);render(<VerifyGoogleEmail token="opaque-proof"/>);
 expect(fetcher).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Doğrula ve devam et'}));await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith('/kayit/google'));expect(fetcher.mock.calls[1][0]).toBe('https://api.first.test/api/auth/google/email/verify/');expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({key:'opaque-proof'});
});
