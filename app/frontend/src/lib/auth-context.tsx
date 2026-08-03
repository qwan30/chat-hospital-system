/**
 * Auth context — wraps the SessionProvider with JWT-based authentication.
 *
 * Dual-mode:
 * - When a JWT token is present in memory → real backend auth
 * - Otherwise → mock role-based session (dev/demo/screenshots)
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  persistToken,
  clearToken,
  verifyToken,
  persistApiUrl,
  getStoredApiUrl,
  resolveApiUrl,
} from "@/lib/api-client";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  department?: string;
  workspace?: string;
  role: string;
  is_active: boolean;
}

export interface AuthState {
  hydrated: boolean;
  authUser: AuthUser | null;
  token: string | null;
  apiUrl: string;
  loading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  setApiUrl: (url: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [hydrated, setHydrated] = useState(false);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [apiUrl, setApiUrlState] = useState(getStoredApiUrl());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setApiUrlState(getStoredApiUrl());
    setHydrated(true);
  }, []);

  const setApiUrl = useCallback((url: string) => {
    setApiUrlState(resolveApiUrl(undefined, url));
    persistApiUrl(url);
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<boolean> => {
    const resolvedApiUrl = getStoredApiUrl();
    setLoading(true);
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch(`${resolvedApiUrl.replace(/\/+$/, "")}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || errData.message || "Invalid credentials");
        setLoading(false);
        return false;
      }

      const data = await res.json();
      const newToken = data.access_token;
      persistToken(newToken);
      setToken(newToken);

      const user = await verifyToken(resolvedApiUrl, newToken);
      if (user) {
        setAuthUser(user);
        setLoading(false);
        return true;
      }

      setError("Failed to verify credentials");
      clearToken();
      setToken(null);
      setLoading(false);
      return false;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed");
      setLoading(false);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setAuthUser(null);
    setToken(null);
    setError(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      hydrated,
      authUser,
      token,
      apiUrl,
      loading,
      error,
      login,
      logout,
      setApiUrl,
    }),
    [hydrated, authUser, token, apiUrl, loading, error, login, logout, setApiUrl],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
