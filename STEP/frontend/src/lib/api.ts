import type { Page } from "./types";
export const API_BASE = (process.env.NEXT_PUBLIC_STEP_API_URL || "http://localhost:8002/api/v1/").replace(/\/?$/, "/");
export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public fields?: Record<string, unknown>) { super(message); this.name = "ApiError"; }
}
let csrfPromise: Promise<string> | null = null;
export function clearCsrf() { csrfPromise = null; }
function endpoint(path: string) {
  const base = new URL(API_BASE);
  const url = new URL(path, base);
  if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) throw new Error("İstek adresi STEP API kapsamı dışında.");
  return url.toString();
}
async function csrf() {
  if (!csrfPromise) csrfPromise = fetch(endpoint("auth/csrf/"), { credentials: "include", cache: "no-store" }).then(async response => {
    if (!response.ok) throw new ApiError(response.status, "csrf_unavailable", "Güvenli oturum kurulamadı. Bağlantıyı kontrol edip yeniden deneyin.");
    const result = await response.json() as { csrf_token: string };
    if (!result.csrf_token) throw new Error("Güvenli oturum bilgisi alınamadı.");
    return result.csrf_token;
  }).catch(error => { csrfPromise = null; throw error; });
  return csrfPromise;
}
export interface RequestOptions { method?: string; body?: unknown; signal?: AbortSignal; key?: string }
export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method || "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  const mutation = method !== "GET" && method !== "HEAD";
  if (mutation) { headers["X-CSRFToken"] = await csrf(); headers["Idempotency-Key"] = options.key || crypto.randomUUID(); }
  const multipart = options.body instanceof FormData;
  if (options.body !== undefined && !multipart) headers["Content-Type"] = "application/json";
  const response = await fetch(endpoint(path), { method, headers, credentials: "include", cache: "no-store", signal: options.signal, body: options.body === undefined ? undefined : multipart ? options.body as FormData : JSON.stringify(options.body) });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({})) as { code?: string; detail?: string; fields?: Record<string, unknown> };
    throw new ApiError(response.status, problem.code || "request_failed", problem.detail || (response.status === 401 ? "Bu işlem için giriş yapın." : "İşlem tamamlanamadı. Yeniden deneyin."), problem.fields);
  }
  if (/^auth\/(login|register|logout|password-reset-confirm)\//.test(path)) clearCsrf();
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}
export async function blob(path: string): Promise<Blob> {
  const response = await fetch(endpoint(path), { credentials: "include", cache: "no-store" });
  if (!response.ok) throw new ApiError(response.status, "media_unavailable", "Bu dosya için erişiminiz yok veya dosya henüz yayımlanmadı.");
  return response.blob();
}
export function errorText(error: unknown): string { return error instanceof Error ? error.message : "Bağlantı kurulamadı. Yeniden deneyin."; }
export function isPage<T>(value: Page<T> | T[]): value is Page<T> { return !Array.isArray(value); }
export function rows<T>(value?: Page<T> | T[] | null): T[] { return value ? Array.isArray(value) ? value : value.results : []; }
export function query(path: string, values: Record<string, string | undefined>) { const parameters = new URLSearchParams(); for (const [key, value] of Object.entries(values)) if (value) parameters.set(key, value); return `${path}${parameters.size ? `?${parameters}` : ""}`; }
export function money(value?: string | number | null) { if (value === undefined || value === null || value === "") return "Belirlenmedi"; return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(Number(value)); }
export function date(value?: string | null) { if (!value) return "—"; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat("tr-TR", { dateStyle: "medium", timeStyle: "short", timeZone: "Europe/Istanbul" }).format(parsed); }
export function shortId(value?: string) { return value ? value.slice(0, 8) : "—"; }
export function localISO(value: string) { return value ? new Date(value).toISOString() : undefined; }
export function safeExternal(value?: string): string | null { if (!value) return null; try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : null; } catch { return null; } }

export function localDateTime(value?: string | null) { if (!value) return ""; const parsed = new Date(value); if (Number.isNaN(parsed.getTime())) return ""; const local = new Date(parsed.getTime() - parsed.getTimezoneOffset() * 60000); return local.toISOString().slice(0,16); }
