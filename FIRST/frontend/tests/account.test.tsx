import {SessionProvider} from '../src/components/session-provider';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AccountForm } from '../src/components/account-form';
import { AccountStatus, SessionList } from '../src/components/account-status';
import { ForgotPassword, ResetPassword, VerifyEmail } from '../src/components/recovery-forms';
const nav = vi.hoisted(() => ({replace: vi.fn(), refresh: vi.fn()}));
vi.mock('next/navigation', () => ({useRouter: () => nav}));
const member = {id: 1, email: 'member@example.test', full_name: 'Test Üye', username: 'üye', birth_date: '2000-01-01', gender: 'unspecified', phone: '', phone_verified: false, email_verified: true, providers:[], has_usable_password:true};
function mockRequests(handler: (path: string, options?: RequestInit) => Response | Promise<Response>) {
  const fetcher = vi.fn((path: string, options?: RequestInit) => path.endsWith('/csrf/') ? Promise.resolve(Response.json({csrfToken: 'fresh'})) : Promise.resolve(handler(path, options)));
  vi.stubGlobal('fetch', fetcher); return fetcher;
}
function submit(name: string) {fireEvent.submit(screen.getByRole('button', {name}).closest('form')!);}
function fill(label: string, value: string) {fireEvent.change(screen.getByLabelText(label), {target: {value}});}

describe('account mutations', () => {
  it('only saves changed profile data, resets after save, and blocks unchanged form submissions', async () => {
    const fetcher = mockRequests((path, options) => path.endsWith('/sessions/') ? Response.json({sessions: []}) : Response.json({user: path.endsWith('/profile/') ? {...member, ...JSON.parse(options!.body as string)} : member}));
    render(<SessionProvider><AccountStatus profile/></SessionProvider>); await screen.findByLabelText('Ad soyad');
    const button = screen.getByRole('button', {name: 'Değişiklikleri kaydet'});
    expect(button).toBeDisabled();
    submit('Değişiklikleri kaydet');
    expect(fetcher.mock.calls.some(([path]) => path.endsWith('/profile/'))).toBe(false);
    fill('Ad soyad', 'Yeni Üye'); expect(button).toBeEnabled();
    fill('Ad soyad', member.full_name); expect(button).toBeDisabled();
    fill('Cinsiyet', 'other'); expect(button).toBeEnabled();
    fill('Cinsiyet', member.gender); expect(button).toBeDisabled();
    fill('Ad soyad', 'Yeni Üye'); submit('Değişiklikleri kaydet');
    await screen.findByText('Bilgiler güncellendi.');
    await waitFor(() => expect(button).toBeDisabled());
    expect(screen.getByLabelText('Ad soyad')).toHaveValue('Yeni Üye');
    fill('Ad soyad', member.full_name); expect(button).toBeEnabled();
  });
  it('keeps unsaved profile changes available after a failed save', async () => {
    mockRequests(path => path.endsWith('/me/') ? Response.json({user: member}) : path.endsWith('/sessions/') ? Response.json({sessions: []}) : Response.json({detail: 'Kaydedilemedi'}, {status: 503}));
    render(<SessionProvider><AccountStatus profile/></SessionProvider>); await screen.findByLabelText('Ad soyad');
    fill('Ad soyad', 'Yeni Üye'); submit('Değişiklikleri kaydet');
    await screen.findByText('Kaydedilemedi');
    expect(screen.getByLabelText('Ad soyad')).toHaveValue('Yeni Üye');
    expect(screen.getByRole('button', {name: 'Değişiklikleri kaydet'})).toBeEnabled();
  });

  it('submits real profile data via PATCH with NFC username and unverified phone', async () => {
    const fetcher = mockRequests(path => path.endsWith('/sessions/') ? Response.json({sessions: []}) : Response.json({user: member}));
    render(<SessionProvider><AccountStatus profile/></SessionProvider>); await screen.findByLabelText('Ad soyad');
    fill('Kullanıcı adı', 'o\u0308grenci'); fill('Telefon (isteğe bağlı)', '+905551234567'); submit('Değişiklikleri kaydet');
    await screen.findByText('Bilgiler güncellendi.');
    const request = fetcher.mock.calls.find(([path]) => path.endsWith('/profile/'))!;
    expect(request[1]?.method).toBe('PATCH');
    expect(JSON.parse(request[1]?.body as string)).toEqual({full_name:'Test Üye', username:'ögrenci', birth_date:'2000-01-01', gender:'unspecified', phone:'+905551234567'});
    expect(new Headers(request[1]?.headers).get('X-CSRFToken')).toBe('fresh');
  });
  it('keeps the old email visible after requesting a new one', async () => {
    const fetcher = mockRequests(path => path.endsWith('/me/') ? Response.json({user:member}) : path.endsWith('/sessions/') ? Response.json({sessions:[]}) : Response.json({detail:'Yeni adrese gönderildi.'}));
    render(<SessionProvider><AccountStatus profile/></SessionProvider>); await screen.findByLabelText('Yeni e-posta'); fill('Yeni e-posta','new@example.test'); submit('Doğrulama bağlantısı gönder');
    await screen.findByText('Yeni adrese gönderildi.'); expect(screen.getByText(/member@example.test · Doğrulandı/)).toBeInTheDocument();
    expect(JSON.parse(fetcher.mock.calls.find(([path]) => path.endsWith('/email/change/'))![1]?.body as string)).toEqual({email:'new@example.test'});
  });
  it('requires explicit retry after successful reauthentication and preserves the operation fields', async () => {
    let changed = false;
    const fetcher = mockRequests(path => {
      if(path.endsWith('/reauthenticate/')) {changed=true; return Response.json({detail:'ok'});}
      return changed ? Response.json({detail:'Değişti'}) : Response.json({detail:'Yeniden doğrulayın',code:'reauthentication_required'},{status:403});
    });
    render(<AccountForm title="E-posta" path="email/change" fields={[{name:'email',label:'Yeni e-posta'}]} submit="Gönder"/>);
    fill('Yeni e-posta','new@example.test'); submit('Gönder'); await screen.findByLabelText('Mevcut şifreniz');
    expect(screen.getByRole('button',{name:'Gönder'})).toBeDisabled(); fill('Mevcut şifreniz','Türkçe42!'); submit('Kimliğimi doğrula');
    await screen.findByText(/İşleminizi yeniden gönderin/); expect(screen.getByLabelText('Yeni e-posta')).toHaveValue('new@example.test');
    expect(fetcher.mock.calls.filter(([path]) => path.endsWith('/email/change/'))).toHaveLength(1);
    submit('Gönder'); await screen.findByText('Değişti');
  });
  it.each([[401,undefined,'Oturum bitti'],[403,'csrf_failed','CSRF reddedildi'],[429,undefined,'Bekleyin'],[503,undefined,'E-posta gönderilemedi']])('shows failure %s without success',async(status,code,detail)=>{
    mockRequests(()=>Response.json({detail,code},{status:status as number}));
    render(<AccountForm title="Gönderim" path="email/resend" submit="Yeniden gönder"/>); submit('Yeniden gönder');
    expect(await screen.findByRole('alert')).toHaveTextContent(detail as string);
    expect(screen.getByRole('button',{name:'Yeniden gönder'})).not.toBeDisabled();
    if(status===401) expect(screen.getByRole('link')).toHaveAttribute('href','/giris');
  });
  it('renders field errors with accessible associations',async()=>{
    mockRequests(()=>Response.json({detail:'Hatalı',errors:{username:['Bu kullanıcı adı kullanılıyor.']}},{status:400}));
    render(<AccountForm title="Profil" path="profile" method="PATCH" fields={[{name:'username',label:'Kullanıcı adı'}]} submit="Kaydet"/>);
    fill('Kullanıcı adı','test'); submit('Kaydet'); await screen.findByRole('alert');
    expect(screen.getByLabelText('Kullanıcı adı')).toHaveAttribute('aria-invalid','true');
    expect(screen.getByLabelText('Kullanıcı adı')).toHaveAccessibleDescription('Bu kullanıcı adı kullanılıyor.');
  });
  it('blocks duplicate mutations while waiting',async()=>{
    let resolve!:(response:Response)=>void;const fetcher=mockRequests(()=>new Promise<Response>(done=>{resolve=done;})); render(<ForgotPassword/>); fill('E-posta','a@example.test');
    submit('Sıfırlama bağlantısı gönder'); fireEvent.submit(screen.getByRole('form'));
    await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2)); expect(screen.getByRole('button')).toBeDisabled();resolve(Response.json({detail:'Tamam'}));await screen.findByText('Tamam');
  });
  it('changes password and returns to login only on success',async()=>{
    nav.replace.mockClear();const fetcher=mockRequests(path=>path.endsWith('/me/')?Response.json({user:member}):path.endsWith('/sessions/')?Response.json({sessions:[]}):Response.json({detail:'Şifre değişti'}));
    render(<SessionProvider><AccountStatus profile/></SessionProvider>); await screen.findByLabelText('Mevcut şifre'); fill('Mevcut şifre','Eski42!x'); fill('Yeni şifre','Yeni42!x'); submit('Şifreyi değiştir');
    await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith('/giris'));
    expect(JSON.parse(fetcher.mock.calls.find(([path])=>path.endsWith('/password/change/'))![1]?.body as string)).toEqual({old_password:'Eski42!x',password:'Yeni42!x'});
  });
});

describe('email links and password recovery',()=>{
  it('requests reset with generic success and only email',async()=>{
    const fetcher=mockRequests(()=>Response.json({detail:'Hesap uygunsa gönderildi.'}));render(<ForgotPassword/>);fill('E-posta','user@example.test');submit('Sıfırlama bağlantısı gönder');await screen.findByText('Hesap uygunsa gönderildi.');
    expect(JSON.parse(fetcher.mock.calls[1][1]?.body as string)).toEqual({email:'user@example.test'});
  });
  it('never mutates or fetches when verification link is opened',()=>{
    const fetcher=mockRequests(()=>Response.json({}));render(<VerifyEmail token="secret"/>);expect(fetcher).not.toHaveBeenCalled();expect(screen.getByRole('button',{name:'E-posta adresini onayla'})).toBeEnabled();
  });
  it.each([member,null])('verifies explicitly then refetches session %s',async(user)=>{
    const fetcher=mockRequests(path=>path.endsWith('/me/')?Response.json({user}):Response.json({detail:'Doğrulandı'}));render(<VerifyEmail token="secret"/>);submit('E-posta adresini onayla');
    await screen.findByText('E-posta adresi doğrulandı.');await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(3));
    expect(fetcher.mock.calls.map(([path])=>path)).toEqual(['https://api.first.test/api/auth/csrf/','https://api.first.test/api/auth/email/verify/','https://api.first.test/api/auth/me/']);
    expect(JSON.parse(fetcher.mock.calls[1][1]?.body as string)).toEqual({key:'secret'});
    expect(await screen.findByRole('link',{name:user?'Hesabıma dön':'Giriş yapın'})).toBeInTheDocument();
  });
  it('expired verification offers actual resend and retry paths',async()=>{
    mockRequests(path=>path.endsWith('/email/verify/')?Response.json({detail:'Süresi doldu',code:'invalid_token'},{status:400}):Response.json({detail:'Tekrar gönderildi'}));
    render(<VerifyEmail token="expired"/>);submit('E-posta adresini onayla');await screen.findByText('Süresi doldu');submit('Doğrulama e-postasını yeniden gönder');await screen.findByText('Tekrar gönderildi');
    expect(screen.getByRole('link',{name:'E-posta değişikliği iste'})).toHaveAttribute('href','/hesap');
  });
  it('reset posts token uid and new password, then logs in anew',async()=>{
    nav.replace.mockClear();const fetcher=mockRequests(()=>Response.json({detail:'Sıfırlandı'}));render(<ResetPassword uid="12" token="secret"/>);expect(fetcher).not.toHaveBeenCalled();fill('Yeni şifre','Yeni42!x');submit('Şifreyi sıfırla');
    await waitFor(()=>expect(nav.replace).toHaveBeenCalledWith('/giris'));expect(JSON.parse(fetcher.mock.calls[1][1]?.body as string)).toEqual({uid:'12',token:'secret',password:'Yeni42!x'});
  });
  it('invalid reset token is recoverable without navigation',async()=>{
    nav.replace.mockClear();mockRequests(()=>Response.json({detail:'Bağlantı geçersiz',code:'invalid_token'},{status:400}));render(<ResetPassword uid="12" token="expired"/>);fill('Yeni şifre','Yeni42!x');submit('Şifreyi sıfırla');
    expect(await screen.findByRole('alert')).toHaveTextContent('Bağlantı geçersiz');expect(screen.getByRole('link')).toHaveAttribute('href','/sifremi-unuttum');expect(nav.replace).not.toHaveBeenCalled();
  });
  it('missing tokens have visible recovery and no mutation',()=>{
    const fetcher=mockRequests(()=>Response.json({}));render(<ResetPassword uid="" token=""/>);expect(screen.getByRole('alert')).toHaveTextContent('eksik');expect(screen.queryByRole('button')).not.toBeInTheDocument();expect(fetcher).not.toHaveBeenCalled();
  });
});

describe('sessions',()=>{
  const record={id:'opaque-id',created_at:'2026-09-17T10:00:00Z',expires_at:'2026-09-18T10:00:00Z',current:false};
  it.each([false,true])('revokes individual session current=%s with CSRF DELETE',async(current)=>{
    const onSignedOut=vi.fn();let removed=false;
    const fetcher=mockRequests(path=>{if(path.endsWith('/sessions/'))return Response.json({sessions:removed?[]:[{...record,current}]});removed=true;return Response.json({detail:'Kapandı'});});
    render(<SessionList onSignedOut={onSignedOut}/>);fireEvent.click(await screen.findByRole('button',{name:current?'Bu oturumu kapat':'Oturumu kapat'}));
    await waitFor(()=>expect(fetcher.mock.calls.some(([path])=>path.endsWith('/sessions/opaque-id/'))).toBe(true));
    expect(fetcher.mock.calls.find(([path])=>path.endsWith('/sessions/opaque-id/'))![1]?.method).toBe('DELETE');
    if(current)await waitFor(()=>expect(onSignedOut).toHaveBeenCalledOnce());else {await screen.findByText('Açık oturum bulunamadı.');expect(onSignedOut).not.toHaveBeenCalled();}
  });
  it('bulk revoke exits after success',async()=>{
    const onSignedOut=vi.fn();mockRequests(path=>path.endsWith('/sessions/')?Response.json({sessions:[]}):Response.json({detail:'Kapandı'}));render(<SessionList onSignedOut={onSignedOut}/>);submit('Bütün oturumları kapat');await waitFor(()=>expect(onSignedOut).toHaveBeenCalledOnce());
  });
  it('session loading failure offers a retry and login link',async()=>{
    mockRequests(()=>Response.json({detail:'Oturum sona erdi'},{status:401}));render(<SessionList onSignedOut={()=>{}}/>);expect(await screen.findByRole('alert')).toHaveTextContent('Oturum sona erdi');expect(screen.getByRole('button',{name:'Oturumları yeniden yükle'})).toBeEnabled();
  });
});
