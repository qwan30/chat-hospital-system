"use client";

import React, { createContext, useContext, useState, useCallback, type ReactNode } from "react";

interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department: string;
}

interface AuthState {
  apiUrl: string;
  token: string;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (apiUrl: string, token: string) => Promise<boolean>;
  logout: () => void;
  setApiUrl: (url: string) => void;
}

const API_URL_STORAGE_KEY = "hospital_ai_api_url";
const E2E_TOKEN_KEY = "e2e_auth_token";
const DEFAULT_API_URL = "http://localhost:8000/api/v1";

function loadPersistedApiUrl(): string {
  if (typeof window === "undefined") return "";
  try {
    return localStorage.getItem(API_URL_STORAGE_KEY) || DEFAULT_API_URL;
  } catch {
    return DEFAULT_API_URL;
  }
}

function persistApiUrl(apiUrl: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(API_URL_STORAGE_KEY, apiUrl);
  } catch {
    // ignore
  }
}

async function verifyToken(apiUrl: string, token: string): Promise<AuthUser | null> {
  try {
    const res = await fetch(`${apiUrl.replace(/\/+$/, "")}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    return res.json() as Promise<AuthUser>;
  } catch {
    return null;
  }
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const persistedApiUrl = loadPersistedApiUrl();

  const [state, setState] = useState<AuthState>({
    apiUrl: persistedApiUrl || DEFAULT_API_URL,
    token: "",
    user: null,
    isAuthenticated: false,
    isLoading: false,
  });

  // Set loading state on mount to block auth guard redirect until auth check completes
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => { setMounted(true); }, []);

  // E2E test auto-login: runs on mount, before auth guard can redirect
  React.useEffect(() => {
    try {
      const e2eToken = typeof window !== "undefined" ? localStorage.getItem(E2E_TOKEN_KEY) : null;
      if (e2eToken) {
        setState((prev) => ({ ...prev, isLoading: true }));
        // Use setTimeout to let the loading state propagate before the async call
        setTimeout(() => {
          login(persistedApiUrl || DEFAULT_API_URL, e2eToken);
        }, 0);
      }
    } catch {
      // ignore
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (apiUrl: string, token: string): Promise<boolean> => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const user = await verifyToken(apiUrl, token);
    if (user) {
      persistApiUrl(apiUrl);
      setState({ apiUrl, token, user, isAuthenticated: true, isLoading: false });
      return true;
    }
    setState((prev) => ({ ...prev, isLoading: false }));
    return false;
  }, []);

  const logout = useCallback(() => {
    setState((prev) => ({
      ...prev,
      token: "",
      user: null,
      isAuthenticated: false,
      isLoading: false,
    }));
  }, []);

  const setApiUrl = useCallback((url: string) => {
    persistApiUrl(url);
    setState((prev) => ({ ...prev, apiUrl: url }));
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, setApiUrl }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
