import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  apiFetch,
  ApiError,
  verifyToken,
  persistToken,
  clearToken,
  getToken,
  getStoredApiUrl,
  persistApiUrl,
} from "./api-client";

// ---------------------------------------------------------------------------
// ApiError class
// ---------------------------------------------------------------------------
describe("ApiError", () => {
  it("creates an error with status, code, and message properties", () => {
    const err = new ApiError(404, "NOT_FOUND", "Resource not found");

    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe("ApiError");
    expect(err.status).toBe(404);
    expect(err.code).toBe("NOT_FOUND");
    expect(err.message).toBe("Resource not found");
  });
});

// ---------------------------------------------------------------------------
// localStorage wrappers
// ---------------------------------------------------------------------------
describe("persistToken / clearToken", () => {
  it("stores the token in memory", () => {
    persistToken("my-jwt");
    expect(getToken()).toBe("my-jwt");
  });

  it("clears the token from memory", () => {
    persistToken("my-jwt");
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe("getStoredApiUrl / persistApiUrl", () => {
  beforeEach(() => {
    vi.stubGlobal("window", {});
    const store: Record<string, string> = {};
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
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the default API URL when nothing is stored", () => {
    expect(getStoredApiUrl()).toBe("/api");
  });

  it("persists and retrieves a custom API URL", () => {
    persistApiUrl("http://custom:3000/api");
    expect(getStoredApiUrl()).toBe("http://custom:3000/api");
  });
});

// ---------------------------------------------------------------------------
// apiFetch — core API client
// ---------------------------------------------------------------------------
describe("apiFetch", () => {
  beforeEach(() => {
    vi.stubGlobal("window", {});
    const store: Record<string, string> = {};
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
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("injects Authorization header when token exists in memory", async () => {
    persistToken("test-jwt");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ user: "test" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/user", {}, { baseUrl: "http://base" });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://base/user",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-jwt",
        }),
      }),
    );
  });

  it("normalizes trailing slashes in base URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/test", {}, { baseUrl: "http://base/api/v1/" });

    expect(fetchMock).toHaveBeenCalledWith("http://base/api/v1/test", expect.anything());
  });

  it("throws ApiError with parsed JSON error body on non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        statusText: "Forbidden",
        json: () => Promise.resolve({ error: "FORBIDDEN", message: "Access denied" }),
      }),
    );

    const err = await apiFetch("/test", {}, { baseUrl: "http://base" }).catch((e) => e);

    expect(err).toBeInstanceOf(ApiError);
    const apiErr = err as ApiError;
    expect(apiErr.status).toBe(403);
    expect(apiErr.code).toBe("FORBIDDEN");
    expect(apiErr.message).toBe("Access denied");
  });

  it("returns undefined for 204 no-content responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
        json: () => Promise.resolve({}),
      }),
    );

    const result = await apiFetch("/test", {}, { baseUrl: "http://base" });
    expect(result).toBeUndefined();
  });

  it("auto-sets Content-Type application/json but not for FormData", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", fetchMock);

    // Without FormData — Content-Type should be application/json
    await apiFetch("/test", {}, { baseUrl: "http://base" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://base/test",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );

    // With FormData — Content-Type should NOT be auto-set
    fetchMock.mockClear();
    const formData = new FormData();
    await apiFetch("/upload", { body: formData }, { baseUrl: "http://base" });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers).not.toHaveProperty("Content-Type");
  });

  it("maps response demo IDs only in identifier fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            patient_id: "20000000-0000-0000-0000-000000000001",
            content: "Reference 20000000-0000-0000-0000-000000000001 exactly",
            citation_text: "90000000-0000-0000-0000-000000000002",
            nested: {
              document_id: "90000000-0000-0000-0000-000000000002",
              title: "Case 90000000-0000-0000-0000-000000000002",
            },
          }),
      }),
    );

    const result = await apiFetch<{
      patient_id: string;
      content: string;
      citation_text: string;
      nested: { document_id: string; title: string };
    }>("/test", {}, { baseUrl: "http://base" });

    expect(result.patient_id).toBe("p-001");
    expect(result.nested.document_id).toBe("ar-002");
    expect(result.content).toBe("Reference 20000000-0000-0000-0000-000000000001 exactly");
    expect(result.citation_text).toBe("90000000-0000-0000-0000-000000000002");
    expect(result.nested.title).toBe("Case 90000000-0000-0000-0000-000000000002");
  });

  it("maps JSON request demo IDs only in identifier fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch(
      "/test",
      {
        method: "POST",
        body: JSON.stringify({
          patient_id: "p-001",
          question: "Compare p-001 with the literal text ar-002",
        }),
      },
      { baseUrl: "http://base" },
    );

    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body)).toEqual({
      patient_id: "20000000-0000-0000-0000-000000000001",
      question: "Compare p-001 with the literal text ar-002",
    });
  });

  it("maps exact graph and generic identifier keys in responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            id: "20000000-0000-0000-0000-000000000003",
            from_node: "90000000-0000-0000-0000-000000000004",
            to_node: "20000000-0000-0000-0000-000000000005",
          }),
      }),
    );

    await expect(apiFetch("/test", {}, { baseUrl: "http://base" })).resolves.toEqual({
      id: "p-003",
      from_node: "ar-004",
      to_node: "p-005",
    });
  });

  it("retains the parent identifier key when mapping response arrays", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            patient_id: [
              "20000000-0000-0000-0000-000000000006",
              "20000000-0000-0000-0000-000000000007",
            ],
          }),
      }),
    );

    await expect(apiFetch("/test", {}, { baseUrl: "http://base" })).resolves.toEqual({
      patient_id: ["p-006", "p-007"],
    });
  });

  it("maps identifiers nested in response array elements", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            evidence: [
              { document_id: "90000000-0000-0000-0000-000000000008" },
              { patient_id: "20000000-0000-0000-0000-000000000009" },
            ],
          }),
      }),
    );

    await expect(apiFetch("/test", {}, { baseUrl: "http://base" })).resolves.toEqual({
      evidence: [{ document_id: "ar-008" }, { patient_id: "p-009" }],
    });
  });

  it("preserves invalid JSON request bodies byte-for-byte", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", fetchMock);
    const body = "not-json p-001 with literal ar-002";

    await apiFetch("/test", { method: "POST", body }, { baseUrl: "http://base" });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.body).toBe(body);
  });

  it("keeps demo-ID translation in request paths unchanged", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/patients/p-010/documents/ar-011", {}, { baseUrl: "http://base" });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://base/patients/20000000-0000-0000-0000-000000000010/documents/90000000-0000-0000-0000-000000000011",
      expect.anything(),
    );
  });
});

// ---------------------------------------------------------------------------
// verifyToken
// ---------------------------------------------------------------------------
describe("verifyToken", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the user object on successful verification", async () => {
    const userData = { user_id: "u1", username: "dr", role: "admin" };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve(userData),
      }),
    );

    const result = await verifyToken("http://api/", "token123");
    expect(result).toEqual(userData);
  });

  it("returns null when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
        json: () => Promise.resolve({}),
      }),
    );

    const result = await verifyToken("http://api", "bad-token");
    expect(result).toBeNull();
  });

  it("returns null on network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network failure")));

    const result = await verifyToken("http://api", "token123");
    expect(result).toBeNull();
  });
});
