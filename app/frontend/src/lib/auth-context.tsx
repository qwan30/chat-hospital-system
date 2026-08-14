/**
 * Auth context — wraps the SessionProvider with JWT-based authentication.
 *
 * Auth modes:
 * - Real Login exchanges credentials for a backend JWT.
 * - Demo Role exchanges an allowlisted persona for a short-lived backend JWT.
 * Legacy local mock-session hydration remains isolated in SessionProvider for
 * existing synthetic E2E fixtures; it is not used by the login route.
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
import type { Role } from "@/lib/rbac";

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
  demoEnabled: boolean;
  demoStatusLoading: boolean;
  demoRole: Role | null;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<boolean>;
  demoLogin: (role: Role) => Promise<boolean>;
  refreshDemoStatus: () => Promise<boolean>;
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
  const [demoEnabled, setDemoEnabled] = useState(false);
  const [demoStatusLoading, setDemoStatusLoading] = useState(false);
  const [demoRole, setDemoRole] = useState<Role | null>(null);

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
    setDemoRole(null);
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

  const refreshDemoStatus = useCallback(async (): Promise<boolean> => {
    const resolvedApiUrl = getStoredApiUrl();
    setDemoStatusLoading(true);
    try {
      const res = await fetch(`${resolvedApiUrl.replace(/\/+$/, "")}/auth/demo/status`, {
        method: "GET",
      });
      if (!res.ok) {
        setDemoEnabled(false);
        return false;
      }
      const data = (await res.json()) as { enabled?: boolean };
      const enabled = data.enabled === true;
      setDemoEnabled(enabled);
      return enabled;
    } catch {
      setDemoEnabled(false);
      return false;
    } finally {
      setDemoStatusLoading(false);
    }
  }, []);

  const demoLogin = useCallback(async (role: Role): Promise<boolean> => {
    const resolvedApiUrl = getStoredApiUrl();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${resolvedApiUrl.replace(/\/+$/, "")}/auth/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || errData.message || "Demo sign-in is unavailable");
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
        setDemoRole(role);
        setLoading(false);
        return true;
      }

      setError("Failed to verify demo credentials");
      clearToken();
      setToken(null);
      setLoading(false);
      return false;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo sign-in failed");
      setLoading(false);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setAuthUser(null);
    setToken(null);
    setDemoRole(null);
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
      demoEnabled,
      demoStatusLoading,
      demoRole,
      login,
      demoLogin,
      refreshDemoStatus,
      logout,
      setApiUrl,
    }),
    [
      hydrated,
      authUser,
      token,
      apiUrl,
      loading,
      error,
      demoEnabled,
      demoStatusLoading,
      demoRole,
      login,
      demoLogin,
      refreshDemoStatus,
      logout,
      setApiUrl,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
