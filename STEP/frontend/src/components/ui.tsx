"use client";
import Link from "next/link";
import { useId, useState, type FormEvent, type ReactNode } from "react";
import { blob, date, rows } from "@/lib/api";
import { useMutation, useResource } from "@/lib/hooks";
import { useSession } from "./session";
import type { Attachment, Page } from "@/lib/types";
export function Heading({ title, description, action }: { title: string; description?: string; action?: ReactNode }) { return <header className="page-heading">
<div>
<h1>{title}</h1>{description ? <p>{description}</p> : null}</div>{action}</header>; }
export function Panel({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) { return <section className={`panel ${className}`}>{title ? <h2>{title}</h2> : null}{children}</section>; }
export function Notice({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "error" | "success" | "warning" }) { return <div className={`notice notice-${tone}`} role={tone === "error" ? "alert" : "status"}>{children}</div>; }
const labels: Record<string, string> = { superseded:"Önceki teklif", simulated:"Yerel kayıt denemesi", release_pending:"Serbest bırakma bekliyor",refund_pending:"İade bekliyor",onboarded:"Ödeme alıcısı kayıtlı",expired:"Süresi doldu",declined:"Reddedildi",resolved:"Sonuçlandı",open:"Açık",draft:"Taslak",cancelled:"İptal",removed:"Kaldırıldı",closed:"Kapalı",fixed:"Sabit ücret",hourly:"Saatlik",submitted:"Gönderildi",withdrawn:"Geri çekildi",rejected:"Reddedildi",selected:"Seçildi",pending:"Bekliyor",active:"Aktif",completed:"Tamamlandı",unfunded:"Fonlama bekliyor",funded:"Fonlandı",in_progress:"Çalışılıyor",revision:"Revizyon",disputed:"İtirazda",released:"Serbest bırakıldı",refunded:"İade edildi",review:"İncelemede",approved:"Onaylandı",requested:"Talep alındı",processing:"Aktarılıyor",paid:"Bankaya aktarıldı",failed:"Başarısız",unavailable:"Hazır değil",unknown:"Sonuç araştırılıyor",preview:"Özel önizleme",held:"Bekletiliyor",withheld:"Özel saklanıyor",verified:"Doğrulandı",unverified:"Doğrulanmadı",access_lost:"E-posta erişimi yok",graduated:"Mezun",accepted:"Kabul edildi",invited:"Davet edildi",simulator:"Yerel deneme",iyzico_sandbox:"Sağlayıcı test ortamı",iyzico_live:"Canlı",confirmed:"Doğrulandı",created:"Oluşturuldu" };
export function Status({ value }: { value?: string }) { return <span className={`status status-${value || "unknown"}`}>{value ? labels[value] || value : "Belirtilmedi"}</span>; }
export function State({ loading, error, empty, children, retry }: { loading?: boolean; error?: string | null; empty?: boolean; children: ReactNode; retry?: () => void }) { if (loading) return <p role="status" className="muted">Yükleniyor…</p>; if (error) return <Notice tone="error">{error}{retry ? <button className="button button-small button-secondary" onClick={retry}>Yeniden dene</button> : null}</Notice>; if (empty) return <p className="empty">Henüz kayıt yok.</p>; return <>{children}</>; }
export function Auth({ children, staff = false }: { children: ReactNode; staff?: boolean }) { const { user, loading } = useSession(); if (loading) return <p role="status">Oturum yükleniyor…</p>; if (!user) return <Notice>Bu alanı kullanmak için <Link href="/auth/login">giriş yapın</Link>.</Notice>; if (staff && !user.is_staff) return <Notice tone="error">Bu alan yalnız yetkili yönetim görevlilerine açıktır.</Notice>; return <>{children}</>; }
export interface FieldSpec { name: string; label: string; type?: "text" | "email" | "password" | "number" | "textarea" | "select" | "checkbox" | "date" | "datetime-local" | "url" | "tel"; required?: boolean; help?: string; value?: string | number | boolean; options?: { value: string; label: string }[]; min?: number; max?: number; step?: string; autoComplete?: string }
export function Field({ field }: { field: FieldSpec }) { const id = useId();
  const scalar = typeof field.value === "boolean" ? undefined : field.value;
  const input = field.type === "textarea" ? <textarea aria-describedby={field.help?`${id}-help`:undefined} id={id} name={field.name} defaultValue={scalar} required={field.required} rows={4} /> : field.type === "select" ? <select aria-describedby={field.help?`${id}-help`:undefined} id={id} name={field.name} defaultValue={scalar || ""} required={field.required}>
<option value="">Seçin</option>{field.options?.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select> : field.type === "checkbox" ? <input aria-describedby={field.help?`${id}-help`:undefined} id={id} name={field.name} type="checkbox" defaultChecked={Boolean(field.value)} /> : <input aria-describedby={field.help?`${id}-help`:undefined} id={id} name={field.name} type={field.type || "text"} defaultValue={scalar} required={field.required} min={field.min} max={field.max} step={field.step} autoComplete={field.autoComplete} />; return <div className={`field ${field.type === "checkbox" ? "field-checkbox" : ""}`}>
<label htmlFor={id}>{field.label}{field.required ? <span aria-hidden="true"> *</span> : null}</label>{input}{field.help ? <small id={`${id}-help`}>{field.help}</small> : null}</div>; }
export function value(data: FormData, key: string) { return String(data.get(key) || "").trim(); }
export function tokens(value: string) { return value.split(",").map(item => item.trim()).filter(Boolean); }
export function TaskForm<T = unknown>({ path, method = "POST", fields, label, message = "İşlem kaydedildi.", build, onSuccess, disabled, children, clearOnSuccess = false }: { path: string; method?: string; fields: FieldSpec[]; label: string; message?: string; build?: (data: FormData) => unknown; onSuccess?: (result: T) => void | Promise<void>; disabled?: boolean; children?: ReactNode; clearOnSuccess?: boolean }) {
  const mutation = useMutation();
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault();
  const element = event.currentTarget;
  const form = new FormData(element); try { const result = await mutation.submit<T>(path, { method, body: build ? build(form) : Object.fromEntries(fields.map(field => [field.name, field.type === "checkbox" ? form.has(field.name) : value(form, field.name)])) }, message); if (clearOnSuccess) element.reset(); if (onSuccess) await onSuccess(result as T); } catch { /* Error is shown by the mutation state. */ } }
  return <form className="task-form" onSubmit={submit}>
<fieldset disabled={disabled || mutation.busy}>
<div className="form-grid">{fields.map(field => <Field key={field.name} field={field} />)}</div>{children}<button className="button" type="submit">{mutation.busy ? "Kaydediliyor…" : label}</button>
</fieldset>{mutation.error ? <Notice tone="error">{mutation.error}</Notice> : null}{mutation.success ? <Notice tone="success">{mutation.success}</Notice> : null}</form>;
}
export function Action({ path, label, body = {}, method = "POST", onSuccess, disabled, message = "İşlem kaydedildi.", secondary = true }: { path: string; label: string; body?: unknown; method?: string; onSuccess?: (result: unknown) => void; disabled?: boolean; message?: string; secondary?: boolean }) { const mutation = useMutation(); return <div className="inline-action">
<button type="button" className={`button button-small ${secondary ? "button-secondary" : ""}`} disabled={disabled || mutation.busy} onClick={async () => { try { const result = await mutation.submit(path, { method, body }, message); onSuccess?.(result); } catch {} }}>{mutation.busy ? "İşleniyor…" : label}</button>{mutation.error ? <Notice tone="error">{mutation.error}</Notice> : null}{mutation.success ? <span role="status" className="success-text">{mutation.success}</span> : null}</div>; }
export function usePaged<T>(base: string | null) { const [navigation, setNavigation] = useState<{ base: string | null; history: string[] }>({ base, history: [] });
  const history = navigation.base === base ? navigation.history : [];
  const current = history.at(-1) || base;
  const resource = useResource<Page<T>>(current); return { ...resource, items: rows(resource.data), next: () => { if (resource.data?.next) setNavigation({ base, history: [...history, resource.data.next] }); }, previous: () => setNavigation({ base, history: history.slice(0, -1) }), hasPrevious: history.length > 0 }; }
export function Pager({ data, next, previous, hasPrevious }: { data?: Page<unknown> | null; next: () => void; previous: () => void; hasPrevious: boolean }) { return data ? <nav className="pager" aria-label="Sayfalama">
<span>{data.count} kayıt</span>
<button className="button button-small button-secondary" disabled={!hasPrevious} onClick={previous}>Önceki</button>
<button className="button button-small button-secondary" disabled={!data.next} onClick={next}>Sonraki</button>
</nav> : null; }
export function Download({ attachment }: { attachment: Attachment }) { const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null); return <span className="download">
<button className="text-button" disabled={busy} onClick={async () => { setBusy(true); setError(null); try { const file = await blob(`attachments/${attachment.id}/download/`);
  const url = URL.createObjectURL(file);
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = attachment.name || attachment.filename || "dosya"; anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000); } catch (problem) { setError(problem instanceof Error ? problem.message : "Dosya alınamadı."); } finally { setBusy(false); } }}>{busy ? "İndiriliyor…" : attachment.name || attachment.filename || "Dosyayı indir"}</button>{error ? <span role="alert">{error}</span> : null}</span>; }
export function FilePicker({ scope, onChange }: { scope: { conversation?: string; contract?: string; job?: string }; onChange: (attachments: Attachment[]) => void }) { const id = useId();
  const [files, setFiles] = useState<Attachment[]>([]);
  const mutation = useMutation(); return <div className="field">
<label htmlFor={id}>Dosya eki</label>
<input id={id} type="file" disabled={mutation.busy} onChange={async event => { const selected = event.target.files?.[0]; if (!selected) return; event.target.value="";
  const data = new FormData(); data.set("file", selected); for (const [key, target] of Object.entries(scope)) if (target) data.set(key, target); try { const attachment = await mutation.submit<Attachment>("attachments/", { method: "POST", body: data }); if (attachment) { const updated = [...files, attachment]; setFiles(updated); onChange(updated); } } catch {} }} />
<small>Dosya ilgili iş veya görüşmeye özel yüklenir. Sunucunun tür ve boyut sınırları uygulanır.</small>{mutation.busy ? <p role="status">Dosya yükleniyor…</p> : null}{mutation.error ? <Notice tone="error">{mutation.error}</Notice> : null}{files.map(file => <div key={file.id}>
<Download attachment={file} />
<button className="text-button" type="button" onClick={() => { const updated = files.filter(item => item.id !== file.id); setFiles(updated); onChange(updated); }}>Eki seçimden çıkar</button>
</div>)}</div>; }
export function Meta({ children }: { children: ReactNode }) { return <div className="meta">{children}</div>; }
export function Time({ value: timestamp }: { value?: string }) { return <time dateTime={timestamp}>{date(timestamp)}</time>; }
