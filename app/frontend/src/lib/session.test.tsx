// @vitest-environment jsdom
import React from "react";
import { act, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { authStateRef, logout, persistToken } = vi.hoisted(() => ({
  authStateRef: {
    current: {
      authUser: null as {
        id: string;
        email: string;
        full_name: string;
        department?: string;
        workspace?: string;
        role: string;
        is_active: boolean;
      } | null,
      token: null as string | null,
      hydrated: true,
      logout: () => undefined,
    },
  },
  logout: vi.fn(),
  persistToken: vi.fn(),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => authStateRef.current,
}));

vi.mock("@/lib/api-client", () => ({
  persistToken,
}));

import { SessionProvider, mapBackendRole, useSession } from "./session";

let captured: ReturnType<typeof useSession> | null = null;

function Capture() {
  captured = useSession();
  return null;
}

function renderCapture() {
  captured = null;
  return render(
    <SessionProvider>
      <Capture />
    </SessionProvider>,
  );
}

function mockLocalStorage(initial?: Record<string, string>) {
  const store: Record<string, string> = { ...initial };
  vi.stubGlobal("localStorage", {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      for (const key of Object.keys(store)) delete store[key];
    }),
  });
  (globalThis as Record<string, unknown>).__mockStore = store;
}

function getMockStore(): Record<string, string> {
  return (globalThis as unknown as Record<string, Record<string, string>>).__mockStore ?? {};
}

describe("SessionProvider / useSession", () => {
  beforeEach(() => {
    captured = null;
    authStateRef.current = {
      authUser: null,
      token: null,
      hydrated: true,
      logout,
    };
    logout.mockReset();
    persistToken.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    captured = null;
  });

  it("renders real authenticated identity while keeping the mapped frontend role", async () => {
    mockLocalStorage();
    authStateRef.current = {
      authUser: {
        id: "doctor-1",
        email: "doctor@example.test",
        full_name: "Dr. Dev Doctor",
        department: "Clinical Informatics",
        role: "doctor",
        is_active: true,
      },
      token: "real-jwt",
      hydrated: true,
      logout,
    };

    renderCapture();

    await waitFor(() => {
      expect(captured?.hydrated).toBe(true);
      expect(captured?.session).not.toBeNull();
    });

    expect(captured!.session).toMatchObject({
      role: "cardiologist",
      isRealAuth: true,
      token: "real-jwt",
      user: {
        name: "Dr. Dev Doctor",
        email: "doctor@example.test",
        initials: "DD",
        title: "Clinical Informatics",
      },
    });
    expect(persistToken).toHaveBeenCalledWith("real-jwt");
    expect(vi.mocked(localStorage.setItem)).not.toHaveBeenCalled();
    expect(getMockStore()).not.toHaveProperty("hms.session");
    expect(Object.values(getMockStore())).not.toContain("real-jwt");
  });

  it("falls back to the mapped mock title when backend department is missing", async () => {
    mockLocalStorage();
    authStateRef.current = {
      authUser: {
        id: "admin-1",
        email: "admin@example.test",
        full_name: "Admin J. Kim",
        role: "admin",
        is_active: true,
      },
      token: "admin-jwt",
      hydrated: true,
      logout,
    };

    renderCapture();

    await waitFor(() => {
      expect(captured?.session).not.toBeNull();
    });

    expect(captured!.session).toMatchObject({
      role: "admin",
      user: {
        name: "Admin J. Kim",
        email: "admin@example.test",
        initials: "AK",
        title: "Workspace Admin",
      },
    });
  });

  it("uses the dedicated demo security token instead of falling through to dev-doctor", async () => {
    mockLocalStorage();
    renderCapture();

    await waitFor(() => {
      expect(captured?.hydrated).toBe(true);
    });

    act(() => {
      captured!.signIn("security");
    });

    await waitFor(() => {
      expect(captured?.session?.token).toBe("dev-security");
    });

    expect(captured!.session?.role).toBe("security");
    expect(persistToken).toHaveBeenCalledWith("dev-security");
  });

  it("signOut logs out auth context and clears persisted mock session metadata", async () => {
    mockLocalStorage();
    renderCapture();

    await waitFor(() => {
      expect(captured?.hydrated).toBe(true);
    });

    act(() => {
      captured!.signIn("admin");
    });

    await waitFor(() => {
      expect(captured?.session?.role).toBe("admin");
    });
    expect(getMockStore()).toHaveProperty("hms.session");

    act(() => {
      captured!.signOut();
    });

    await waitFor(() => {
      expect(captured?.session).toBeNull();
    });

    expect(logout).toHaveBeenCalledTimes(1);
    expect(vi.mocked(localStorage.removeItem)).toHaveBeenCalledWith("hms.session");
    expect(getMockStore()).not.toHaveProperty("hms.session");
  });
});

describe("mapBackendRole", () => {
  it("maps canonical backend non-clinical roles without clinical fallback", () => {
    expect(mapBackendRole("records_staff")).toBe("front_desk");
    expect(mapBackendRole("security")).toBe("security");
    expect(mapBackendRole("front_desk")).toBe("front_desk");
  });
});
