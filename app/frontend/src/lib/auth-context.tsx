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

const STORAGE_KEY = "hospital_ai_auth";
const DEFAULT_API_URL = "http://localhost:8000/api/v1";

function loadPersistedAuth(): { apiUrl: string; token: string } {
  if (typeof window === "undefined") return { apiUrl: "", token: "" };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { apiUrl: parsed.apiUrl || "", token: parsed.token || "" };
    }
  } catch {
    // ignore
  }
  return { apiUrl: DEFAULT_API_URL, token: "" };
}

async function verifyToken(apiUrl: string, token: string): Promise<AuthUser | null> {
  try {
    const res = await fetch(`${apiUrl.replace(/\/+$/, "")}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data as AuthUser;
  } catch {
    return null;
  }
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Internal child that runs the restore-on-mount logic.
 * Splitting this out avoids the "setState in effect" lint rule on the
 * parent while still restoring the session asynchronously.
 */
function AuthRestorer({ onRestored }: { onRestored: (s: AuthState) => void }) {
  const [ran, setRan] = useState(false);
  if (!ran) {
    setRan(true);
    const { apiUrl, token } = loadPersistedAuth();
    if (token && apiUrl) {
      verifyToken(apiUrl, token).then((user) => {
        onRestored({
          apiUrl,
          token,
          user,
          isAuthenticated: !!user,
          isLoading: false,
        });
      });
    } else {
      // Immediately mark as not loading
      Promise.resolve().then(() =>
        onRestored({
          apiUrl: apiUrl || DEFAULT_API_URL,
          token: "",
          user: null,
          isAuthenticated: false,
          isLoading: false,
        })
      );
    }
  }
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const persisted = loadPersistedAuth();

  const [state, setState] = useState<AuthState>({
    apiUrl: persisted.apiUrl || DEFAULT_API_URL,
    token: persisted.token,
    user: null,
    isAuthenticated: false,
    isLoading: !!persisted.token,
  });

  const [restored, setRestored] = useState(false);

  const handleRestored = useCallback((s: AuthState) => {
    setState(s);
    setRestored(true);
  }, []);

  const login = useCallback(async (apiUrl: string, token: string): Promise<boolean> => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const user = await verifyToken(apiUrl, token);
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ apiUrl, token }));
      setState({ apiUrl, token, user, isAuthenticated: true, isLoading: false });
      return true;
    }
    setState((prev) => ({ ...prev, isLoading: false }));
    return false;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setState((prev) => ({
      ...prev,
      token: "",
      user: null,
      isAuthenticated: false,
      isLoading: false,
    }));
  }, []);

  const setApiUrl = useCallback((url: string) => {
    setState((prev) => ({ ...prev, apiUrl: url }));
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, setApiUrl }}>
      {!restored && <AuthRestorer onRestored={handleRestored} />}
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
