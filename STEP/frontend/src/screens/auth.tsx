"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useSession } from "@/components/session";
import { Heading, Notice, Panel, TaskForm, value } from "@/components/ui";
import type { User } from "@/lib/types";
export function AuthScreen({ mode }: { mode: "login" | "register" | "reset" | "reset-confirm" | "student-confirm" }) {
  const router = useRouter();
  const { refresh } = useSession();
  const [token, setToken] = useState("");
  useEffect(() => { setToken(new URLSearchParams(window.location.search).get("token") || ""); }, []);
  if (mode === "login") return <>
<Heading title="Giriş yap" description="STEP e-posta ve şifrenizle çalışma alanınıza ulaşın." />
<Panel>
<TaskForm<User> path="auth/login/" fields={[{name:"email",label:"E-posta",type:"email",required:true,autoComplete:"email"},{name:"password",label:"Şifre",type:"password",required:true,autoComplete:"current-password"}]} label="Giriş yap" message="Oturum açıldı." onSuccess={async () => { await refresh(); router.push("/dashboard"); }} />
<div className="actions">
<Link href="/auth/reset">Şifremi unuttum</Link>
<Link href="/auth/register">Hesap oluştur</Link>
</div>
</Panel>
</>;
  if (mode === "register") return <>
<Heading title="STEP hesabı oluştur" description="Aynı hesapla öğrenci ve işveren rollerini kullanabilirsiniz." />
<Panel>
<TaskForm<User> path="auth/register/" fields={[{name:"display_name",label:"Ad soyad",required:true,autoComplete:"name"},{name:"email",label:"E-posta",type:"email",required:true,autoComplete:"email"},{name:"password",label:"Şifre",type:"password",required:true,autoComplete:"new-password",help:"Güçlü ve başka hesaplarda kullanmadığınız bir şifre seçin."},{name:"student",label:"Öğrenci olarak iş almak istiyorum",type:"checkbox",value:true},{name:"employer",label:"İşveren olarak ilan açmak istiyorum",type:"checkbox"}]} build={data => ({display_name:value(data,"display_name"),email:value(data,"email"),password:value(data,"password"),roles:[...(data.has("student")?["student"]:[]),...(data.has("employer")?["employer"]:[])]})} label="Hesap oluştur" message="Hesabınız oluşturuldu." onSuccess={async () => { await refresh(); router.push("/account"); }} />
<p>
<Link href="/auth/login">Zaten hesabım var</Link>
</p>
</Panel>
</>;
  if (mode === "reset") return <>
<Heading title="Şifremi sıfırla" description="E-posta adresinize şifre sıfırlama bağlantısı isteyin." />
<Panel>
<TaskForm path="auth/password-reset/" fields={[{name:"email",label:"E-posta",type:"email",required:true,autoComplete:"email"}]} label="Sıfırlama bağlantısı iste" message="İstek alındı. Bu adreste bir hesap varsa sıfırlama bağlantısı e-postayla iletilir." />
<p>
<Link href="/auth/login">Girişe dön</Link>
</p>
</Panel>
</>;
  const student = mode === "student-confirm";
  return <>
<Heading title={student ? "Üniversite e-postasını doğrula" : "Yeni şifre belirle"} />
<Panel>{student ? <Notice>Bu işlem üniversite e-postanıza erişiminizi doğrular. Öğrenci kaydınıza bağımsız bir sorgu yapılmaz.</Notice> : null}<TaskForm key={token} path={student ? "verification/student-confirm/" : "auth/password-reset-confirm/"} fields={[{name:"token",label:"E-postadaki doğrulama kodu",required:true,value:token},...(!student ? [{name:"password",label:"Yeni şifre",type:"password" as const,required:true,autoComplete:"new-password"}] : [])]} label={student ? "E-postamı doğrula" : "Şifreyi kaydet"} message={student ? "Üniversite e-posta doğrulaması kaydedildi." : "Şifreniz değişti. Yeniden giriş yapın."} onSuccess={async () => { await refresh(); if (!student) router.push("/auth/login"); }} />
</Panel>
</>;
}
