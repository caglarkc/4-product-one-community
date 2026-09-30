"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, errorText, rows, type RequestOptions } from "./api";
export function useResource<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(Boolean(path)); const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision(value => value + 1), []);
  useEffect(() => {
    setData(null); setError(null); setLoading(Boolean(path)); if (!path) return;
    const controller = new AbortController();
    api<T>(path, { signal: controller.signal }).then(value => { if (!controller.signal.aborted) setData(value); }).catch(problem => { if (!controller.signal.aborted) setError(errorText(problem)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [path, revision]);
  return { data, error, loading, reload, setData };
}
export function useMutation() {
  const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null); const [success, setSuccess] = useState<string | null>(null);
  const locked = useRef(false); const intent = useRef<{ digest: string; key: string } | null>(null);
  const submit = useCallback(async <T,>(path: string, options: RequestOptions, message?: string): Promise<T | undefined> => {
    if (locked.current) return; locked.current = true; setBusy(true); setError(null); setSuccess(null);
    try {
    const payload = `${path}:${options.method || "POST"}:${options.body instanceof FormData ? Array.from(options.body.entries()).map(([name, value]) => `${name}:${typeof value === "string" ? value : `${value.name}/${value.size}/${value.lastModified}`}`).join("|") : JSON.stringify(options.body)}`;
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload)))).map(byte => byte.toString(16).padStart(2, "0")).join("");
    const currentIntent = intent.current?.digest === digest ? intent.current : { digest, key: crypto.randomUUID() }; intent.current = currentIntent;
    const result = await api<T>(path, { ...options, key: currentIntent.key }); intent.current = null; if (message) setSuccess(message); return result; }
    catch (problem) {
      if (problem instanceof ApiError && problem.status >= 400 && problem.status < 500 && ![408, 429].includes(problem.status) && !/(unknown|processing)/.test(problem.code) && problem.code !== "request_failed") intent.current = null;
      setError(errorText(problem)); throw problem;
    }
    finally { locked.current = false; setBusy(false); }
  }, []);
  return { busy, error, success, submit, setError, setSuccess };
}

export function useCollection<T>(path: string | null) {
  const [state,setState] = useState<{path:string|null;items:T[];loading:boolean;error:string|null}>({path:null,items:[],loading:false,error:null});
  const [revision,setRevision]=useState(0); const reload=useCallback(()=>setRevision(value=>value+1),[]);
  useEffect(()=>{ const controller=new AbortController(); setState({path,items:[],loading:Boolean(path),error:null}); if(!path)return;
    async function load(){try{let next:string|null=path;const items:T[]=[];const seen=new Set<string>();while(next){if(seen.has(next))throw new Error("Liste sayfalaması tamamlanamadı.");seen.add(next);const page=await api<import("./types").Page<T>>(next,{signal:controller.signal});items.push(...rows(page));next=page.next;}if(!controller.signal.aborted)setState({path,items,loading:false,error:null});}catch(error){if(!controller.signal.aborted)setState({path,items:[],loading:false,error:errorText(error)});}}
    void load();return()=>controller.abort();
  },[path,revision]);
  return {items:state.path===path?state.items:[],loading:state.path!==path?Boolean(path):state.loading,error:state.path===path?state.error:null,reload};
}
