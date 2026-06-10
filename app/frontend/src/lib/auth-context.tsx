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
