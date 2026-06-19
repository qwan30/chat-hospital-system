// @vitest-environment jsdom
import { describe, expect, it, vi, beforeAll, afterAll, beforeEach, afterEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "./auth-context";

// ---------------------------------------------------------------------------
// Test component: captures context into a module-level mutable ref so tests
// can inspect state and call methods imperatively.
// ---------------------------------------------------------------------------
let captured: ReturnType<typeof useAuth> | null = null;

function Capture() {
  captured = useAuth();
  return null;
}

function renderCapture() {
  captured = null;
  return render(
    <AuthProvider>
      <Capture />
    </AuthProvider>,
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
/** Stub localStorage with an in-memory store. */
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
      for (const k in store) delete store[k];
    }),
  });
  // Expose the store for test assertions
  (globalThis as unknown as Record<string, unknown>).__mockStore = store;
}

function getMockStore(): Record<string, string> {
  return (globalThis as unknown as Record<string, Record<string, string>>).__mockStore ?? {};
}

/** Stub fetch with a single response. */
function mockFetch(response: { ok: boolean; status: number; json: () => Promise<unknown> }) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

/** Stub fetch with a URL-aware dispatcher (for multi-endpoint scenarios). */
function mockFetchWith(dispatcher: (url: string, init?: RequestInit) => Promise<unknown>) {
  vi.stubGlobal("fetch", vi.fn(dispatcher));
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("AuthProvider / useAuth", () => {
  let origConsoleError: typeof console.error;

  beforeAll(() => {
    origConsoleError = console.error;
  });

  afterAll(() => {
    console.error = origConsoleError;
  });

  beforeEach(() => {
    captured = null;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    captured = null;
  });

  // --- 1. Default state ---
  it("renders children and provides auth context with clean initial state", () => {
    mockLocalStorage();
    renderCapture();
    expect(captured).not.toBeNull();
    expect(captured!.authUser).toBeNull();
    expect(captured!.token).toBeNull();
    expect(captured!.error).toBeNull();
    expect(captured!.loading).toBe(false);
  });

  // --- 2. useAuth throws outside provider ---
  it("throws when useAuth is called outside AuthProvider", () => {
    mockLocalStorage();
    console.error = () => {}; // suppress React error boundary logs
    // Render Capture (which calls useAuth) without wrapping in AuthProvider.
    // React re-throws the error through act/testing-library render.
    expect(() => render(<Capture />)).toThrow("useAuth must be used within AuthProvider");
    console.error = origConsoleError;
  });

  // --- 5. Hydration with no stored token ---
  it("sets hydrated=true and authUser=null after mount when no token is stored", async () => {
    mockLocalStorage();
    renderCapture();
    await waitFor(() => {
      expect(captured!.hydrated).toBe(true);
      expect(captured!.authUser).toBeNull();
      expect(captured!.token).toBeNull();
    });
  });

  // --- 6. Hydration with valid stored token ---
  it("sets authUser after mount when a valid stored token exists", async () => {
    mockLocalStorage({ hospital_ai_token: "valid-jwt" });
    mockFetch({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ user_id: "u1", username: "dr", role: "admin" }),
    });
    renderCapture();
    await waitFor(() => {
      expect(captured!.hydrated).toBe(true);
      expect(captured!.authUser).toEqual({ user_id: "u1", username: "dr", role: "admin" });
    });
    expect(captured!.token).toBe("valid-jwt");
  });

  // --- 3. Logout ---
  it("logout clears authUser, token, and error", async () => {
    mockLocalStorage({ hospital_ai_token: "valid-jwt" });
    mockFetch({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ user_id: "u1", username: "dr", role: "admin" }),
    });
    renderCapture();
    await waitFor(() => {
      expect(captured!.hydrated).toBe(true);
      expect(captured!.authUser).not.toBeNull();
    });

    captured!.logout();
    await waitFor(() => {
      expect(captured!.authUser).toBeNull();
      expect(captured!.token).toBeNull();
      expect(captured!.error).toBeNull();
    });
  });

  // --- 4. setApiUrl ---
  it("setApiUrl persists the URL to localStorage and updates state", async () => {
    mockLocalStorage();
    renderCapture();
    await waitFor(() => expect(captured).not.toBeNull());

    captured!.setApiUrl("http://custom:3000/api");
    await waitFor(() => {
      expect(captured!.apiUrl).toBe("http://custom:3000/api");
    });
    expect(getMockStore()["hospital_ai_api_url"]).toBe("http://custom:3000/api");
  });

  // --- 7. Login failure ---
  it("login failure sets error message and returns false", async () => {
    mockLocalStorage();
    renderCapture();
    await waitFor(() => expect(captured).not.toBeNull());

    // Stub fetch for the token endpoint before calling login
    mockFetch({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: "Invalid credentials" }),
    });

    const result = await captured!.login("bad", "creds");
    expect(result).toBe(false);
    await waitFor(() => {
      expect(captured!.error).toBe("Invalid credentials");
    });
    expect(captured!.authUser).toBeNull();
  });

  // --- 7b. Login with invalid token (verifyToken returns null) ---
  it("login fails when verifyToken returns null after successful auth", async () => {
    mockLocalStorage();
    renderCapture();
    await waitFor(() => expect(captured).not.toBeNull());

    // First call = POST /auth/token returns access_token
    // Second call = GET /auth/me (via verifyToken) returns null
    let callCount = 0;
    mockFetchWith(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access_token: "issued-jwt", token_type: "bearer" }),
        });
      }
      // Second call (verifyToken) fails
      return Promise.resolve({
        ok: false,
        status: 401,
        json: () => Promise.resolve({}),
      });
    });

    const result = await captured!.login("valid_user", "correct_pw");
    expect(result).toBe(false);
    await waitFor(() => {
      expect(captured!.error).toBe("Failed to verify credentials");
    });
    expect(captured!.authUser).toBeNull();
    // Token should be cleared when verifyToken fails
    expect(captured!.token).toBeNull();
  });
});
