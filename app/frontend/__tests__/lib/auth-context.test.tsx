import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import React from "react";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe("useAuth hook", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("provides initial unauthenticated state", () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });

  it("login succeeds with valid token", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: "1", full_name: "Dr. Test", email: "test@hosp.com", role: "physician", department: "Cardiology" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login("http://localhost:8000/api/v1", "test-token");
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.full_name).toBe("Dr. Test");
    vi.unstubAllGlobals();
  });

  it("login fails with invalid token", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ error: "UNAUTHORIZED" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login("http://localhost:8000/api/v1", "bad-token");
    });

    expect(result.current.isAuthenticated).toBe(false);
    vi.unstubAllGlobals();
  });

  it("logout clears state", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true, status: 200,
      json: () => Promise.resolve({ id: "1", full_name: "Dr. Test", email: "t@h.com", role: "dr", department: "Card" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login("http://localhost", "token");
    });
    expect(result.current.isAuthenticated).toBe(true);

    await act(async () => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    vi.unstubAllGlobals();
  });
});
