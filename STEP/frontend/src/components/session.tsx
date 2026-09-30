"use client";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, ApiError, errorText } from "@/lib/api";
import type { Config, User } from "@/lib/types";
interface Session { user: User | null; config: Config | null; loading: boolean; error: string | null; refresh: () => Promise<void> }
const SessionContext = createContext<Session | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const refresh = useCallback(async () => {
    setLoading(true); setError(null);
    const [settings, account] = await Promise.allSettled([api<Config>("config/"), api<User>("auth/me/")]);
    if (settings.status === "fulfilled") setConfig(settings.value); else { setConfig(null); setError(errorText(settings.reason)); }
    if (account.status === "fulfilled") setUser(account.value); else { setUser(null); if (!(account.reason instanceof ApiError && [401, 403].includes(account.reason.status))) setError(errorText(account.reason)); }
    setLoading(false);
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  return <SessionContext.Provider value={{ user, config, loading, error, refresh }}>{children}</SessionContext.Provider>;
}
export function useSession() { const session = useContext(SessionContext); if (!session) throw new Error("Oturum sağlayıcısı bulunamadı."); return session; }
