vi.mock('../src/components/google-auth',()=>({GoogleButton:()=>null}));
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { it, expect, vi } from 'vitest';
import ResetPage from '../src/app/sifre-sifirla/page';
import VerifyPage from '../src/app/eposta-dogrula/page';
import { ResetPassword } from '../src/components/recovery-forms';
import { AuthForm } from '../src/components/auth-form';
vi.mock('next/navigation',()=>({useRouter:()=>({replace:vi.fn(),refresh:vi.fn()})}));
it('route extracts verification key without request on mount',async()=>{
  const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);
  render(await VerifyPage({searchParams:Promise.resolve({key:'example'})}));
  expect(screen.getByRole('button',{name:'E-posta adresini onayla'})).toBeEnabled();expect(fetcher).not.toHaveBeenCalled();
});
it('array reset parameters are rejected instead of string-coerced',async()=>{
  const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);render(await ResetPage({searchParams:Promise.resolve({uid:['1','2'],token:'example'})}));
  expect(screen.getByRole('alert')).toHaveTextContent('eksik');expect(fetcher).not.toHaveBeenCalled();
});
it.each([false,true])('allows20 Unicode codepoints even when UTF16 length exceeds20 register=%s',async(register)=>{
  const user=(await import('@testing-library/user-event')).default.setup();
  const fetcher=vi.fn().mockResolvedValueOnce(Response.json({csrfToken:'fresh'})).mockResolvedValueOnce(Response.json(register?{user:{id:1}}:{detail:'ok'}));vi.stubGlobal('fetch',fetcher);
  render(register?<AuthForm register/>:<ResetPassword uid="1" token="example"/>);
  const password='Abc1!'+'😀'.repeat(15);const input=screen.getByLabelText(register?'Şifre':'Yeni şifre');
  await user.type(input,password);expect(input).toHaveValue(password);expect(input).not.toHaveAttribute('maxlength');expect(input).not.toHaveAttribute('minlength');
  if(register)for(const [label,value] of [['E-posta','a@example.test'],['Kullanıcı adı','testuser'],['Ad soyad','Test Üye'],['Doğum tarihi','2000-01-01'],['Cinsiyet','unspecified']])fireEvent.change(screen.getByLabelText(label),{target:{value}});
  await user.click(screen.getByRole('button',{name:register?'Kayıt ol':'Şifreyi sıfırla'}));await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));expect(JSON.parse(fetcher.mock.calls[1][1].body).password).toBe(password);
});
