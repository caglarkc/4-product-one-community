import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AccountReset } from '../src/components/account-reset';
import LoginPage from '../src/app/giris/page';
import { AccountStatus } from '../src/components/account-status';
import { ReauthenticationContext } from '../src/components/account-form';
import type { User } from '../src/lib/api';
const nav = vi.hoisted(() => ({replace: vi.fn(), refresh: vi.fn()}));
vi.mock('next/navigation', () => ({useRouter: () => nav}));
const user: User = {id:1,email:'member@example.test',username:'member',full_name:'Test Üye',birth_date:'2000-01-01',gender:'unspecified',phone:'',email_verified:true,phone_verified:false,profile_complete:true,providers:['github'],has_usable_password:true,capabilities:{can_apply:true,can_create_listing:true}};
function requests(handler: (path:string, options?:RequestInit) => Response | Promise<Response>) {
  const fetcher = vi.fn((path:string, options?:RequestInit) => Promise.resolve(path.endsWith('/csrf/') ? Response.json({csrfToken:'fresh'}) : handler(path,options)));
  vi.stubGlobal('fetch',fetcher); return fetcher;
}
function click(name:string) {fireEvent.click(screen.getByRole('button',{name}));}
function submit(name:string) {fireEvent.submit(screen.getByRole('button',{name}).closest('form')!);}
function view() {const onChanged=vi.fn(),onDeleted=vi.fn();render(<AccountReset user={user} onChanged={onChanged} onDeleted={onDeleted}/>);return {onChanged,onDeleted};}

describe('account reset controls', () => {
  it('opens and cancels each distinct confirmation without issuing requests', () => {
    const fetcher=requests(()=>Response.json({}));view();
    for(const name of ['GitHub hesap bağlantısını kaldır','GitHub repo izinlerini kaldır','FIRST hesabımı sil']) {click(name);click('Vazgeç');}
    expect(fetcher).not.toHaveBeenCalled();
  });
  it.each([
    ['GitHub hesap bağlantısını kaldır','GitHub bağlantısını kaldırmayı onayla','github/disconnect','GITHUB'],
    ['GitHub repo izinlerini kaldır','Repo izinlerini kaldırmayı onayla','projects/github/disconnect','REPO'],
  ])('confirms %s with fresh CSRF and updates the current user',async(title,button,path,confirmation)=>{
    const updated={...user,providers:path==='github/disconnect'?[]:['github']};
    const fetcher=requests(()=>Response.json({detail:'Bağlantı kaldırıldı.',user:updated}));const {onChanged,onDeleted}=view();
    click(title);expect(fetcher).not.toHaveBeenCalled();submit(button);
    await screen.findByText('Bağlantı kaldırıldı.');expect(onChanged).toHaveBeenCalledWith(updated);expect(onDeleted).not.toHaveBeenCalled();
    expect(fetcher.mock.calls[1]).toEqual([`/api/auth/${path}/`,expect.objectContaining({method:'POST',body:JSON.stringify({confirmation}),headers:{'Content-Type':'application/json','X-CSRFToken':'fresh'}})]);
  });
  it('requires exact typed deletion confirmation even if submit is dispatched directly',async()=>{
    const fetcher=requests(()=>Response.json({detail:'Hesap silindi.'}));const {onDeleted}=view();click('FIRST hesabımı sil');
    submit('Hesabımı kalıcı olarak sil');expect(fetcher).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText('Onaylamak için HESABIMI SIL yazın'),{target:{value:'HESABIMI SIL'}});submit('Hesabımı kalıcı olarak sil');
    await waitFor(()=>expect(onDeleted).toHaveBeenCalledOnce());expect(fetcher.mock.calls[1]).toEqual(['/api/auth/account/',expect.objectContaining({method:'DELETE',body:JSON.stringify({confirmation:'HESABIMI SIL'})})]);
  });
  it('blocks duplicate confirmations and cancel during a pending request',async()=>{
    const fetcher=requests(()=>new Promise(()=>{}));view();click('GitHub repo izinlerini kaldır');submit('Repo izinlerini kaldırmayı onayla');
    fireEvent.submit(screen.getByRole('form',{name:'GitHub repo izinlerini kaldır onayı'}));
    await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));expect(screen.getByRole('button',{name:'Vazgeç'})).toBeDisabled();expect(screen.getByRole('button',{name:'FIRST hesabımı sil'})).toBeDisabled();expect(screen.getByRole('button',{name:'GitHub hesap bağlantısını kaldır'})).toBeDisabled();
  });
  it.each(['last_login_method','github_unavailable'])('preserves account and confirmation after %s failure',async(code)=>{
    requests(()=>Response.json({detail:'İşlem yapılamadı.',code},{status:409}));const {onChanged,onDeleted}=view();click('GitHub hesap bağlantısını kaldır');submit('GitHub bağlantısını kaldırmayı onayla');
    await screen.findByText('İşlem yapılamadı.');expect(onChanged).not.toHaveBeenCalled();expect(onDeleted).not.toHaveBeenCalled();
    expect(screen.getByRole('button',{name:'GitHub bağlantısını kaldırmayı onayla'})).toBeEnabled();
    if(code==='last_login_method') expect(screen.getByRole('link',{name:'E-posta bağlantısıyla şifre oluşturun'})).toHaveAttribute('href','/sifremi-unuttum');
  });
  it('reauthenticates without silently retrying the destructive action',async()=>{
    let verified=false;
    const fetcher=requests(path=>{if(path.endsWith('/reauthenticate/')) {verified=true;return Response.json({detail:'Doğrulandı.'});}return verified?Response.json({detail:'Kaldırıldı.',user}):Response.json({detail:'Yeniden doğrulayın',code:'reauthentication_required'},{status:403});});
    view();click('GitHub repo izinlerini kaldır');submit('Repo izinlerini kaldırmayı onayla');await screen.findByLabelText('Mevcut şifreniz');
    fireEvent.change(screen.getByLabelText('Mevcut şifreniz'),{target:{value:'Example42!'}});submit('Kimliğimi doğrula');
    await waitFor(()=>expect(screen.getByRole('button',{name:'Repo izinlerini kaldırmayı onayla'})).toBeEnabled());
    expect(fetcher.mock.calls.filter(([path])=>path.endsWith('/projects/github/disconnect/'))).toHaveLength(1);
    submit('Repo izinlerini kaldırmayı onayla');await screen.findByText('Kaldırıldı.');
  });
  it('offers password recovery for a GitHub-only user without bypassing reauthentication',async()=>{
    requests(()=>Response.json({detail:'Yeniden doğrulayın',code:'reauthentication_required'},{status:403}));
    render(<ReauthenticationContext.Provider value={{google:false,password:false}}><AccountReset user={{...user,has_usable_password:false}} onChanged={vi.fn()} onDeleted={vi.fn()}/></ReauthenticationContext.Provider>);
    click('FIRST hesabımı sil');fireEvent.change(screen.getByLabelText('Onaylamak için HESABIMI SIL yazın'),{target:{value:'HESABIMI SIL'}});submit('Hesabımı kalıcı olarak sil');
    expect(await screen.findByRole('link',{name:'e-posta bağlantısıyla bir şifre oluşturun'})).toHaveAttribute('href','/sifremi-unuttum');expect(screen.getByRole('button',{name:'Hesabımı kalıcı olarak sil'})).toBeDisabled();
  });
  it('refreshes session data and linked account presentation after identity disconnect',async()=>{
    const fetcher=requests(path=>path.endsWith('/me/')?Response.json({user}):path.endsWith('/sessions/')?Response.json({sessions:[]}):Response.json({detail:'Kaldırıldı.',user:{...user,providers:[]}}));
    render(<AccountStatus profile/>);fireEvent.click(await screen.findByRole('button',{name:'GitHub hesap bağlantısını kaldır'}));submit('GitHub bağlantısını kaldırmayı onayla');
    await screen.findByText('GitHub profilinizi FIRST hesabınıza bağlayın.');await waitFor(()=>expect(fetcher.mock.calls.filter(([path])=>path.endsWith('/sessions/'))).toHaveLength(2));
  });
  it('retains the remote cleanup warning after identity removal unmounts the control',async()=>{
    requests(path=>path.endsWith('/me/')?Response.json({user}):path.endsWith('/sessions/')?Response.json({sessions:[]}):Response.json({detail:'FIRST bağlantısı kaldırıldı, GitHub temizliği gerekiyor.',github_cleanup_required:true,user:{...user,providers:[]}}));
    render(<AccountStatus profile/>);fireEvent.click(await screen.findByRole('button',{name:'GitHub hesap bağlantısını kaldır'}));submit('GitHub bağlantısını kaldırmayı onayla');
    expect(await screen.findByRole('status')).toHaveTextContent('GitHub temizliği gerekiyor');expect(screen.getByRole('link',{name:'GitHub’da kalan izni kaldırın (yeni sekme)'})).toBeInTheDocument();expect(screen.queryByRole('button',{name:'GitHub hesap bağlantısını kaldır'})).not.toBeInTheDocument();
  });
  it('renders a deletion completion warning with a GitHub settings link',async()=>{
    requests(()=>Response.json({}));render(await LoginPage({searchParams:Promise.resolve({account_deleted:'1',github_cleanup:'1'})}));
    expect(screen.getByRole('status')).toHaveTextContent('FIRST hesabınız silindi');expect(screen.getByRole('status')).toHaveTextContent('GitHub izni otomatik kaldırılamadı');
  });
  it.each([false,true])('clears the account view and redirects only after confirmed successful deletion (cleanup=%s)',async(cleanup)=>{
    nav.replace.mockClear();requests(path=>path.endsWith('/me/')?Response.json({user}):path.endsWith('/sessions/')?Response.json({sessions:[]}):Response.json({detail:'Silindi.',github_cleanup_required:cleanup}));
    render(<AccountStatus profile/>);fireEvent.click(await screen.findByRole('button',{name:'FIRST hesabımı sil'}));fireEvent.change(screen.getByLabelText('Onaylamak için HESABIMI SIL yazın'),{target:{value:'HESABIMI SIL'}});submit('Hesabımı kalıcı olarak sil');
    await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith(`/giris?account_deleted=1${cleanup?'&github_cleanup=1':''}`));expect(screen.queryByText('Merhaba, Test Üye.')).not.toBeInTheDocument();
  });
});
