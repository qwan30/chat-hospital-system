import { describe, it, expect, vi } from "vitest";
import { ApiError, apiFetch } from "@/lib/api-client";

describe("ApiError", () => {
  it("creates an error with status, code, and message", () => {
    const error = new ApiError(404, "NOT_FOUND", "Resource not found");
    expect(error).toBeInstanceOf(Error);
    expect(error.name).toBe("ApiError");
    expect(error.status).toBe(404);
    expect(error.code).toBe("NOT_FOUND");
    expect(error.message).toBe("Resource not found");
  });
});

describe("apiFetch", () => {
  it("sends request with auth header", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: "test" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await apiFetch("/test", {
      apiUrl: "http://localhost:8000/api/v1",
      token: "test-token",
      method: "GET",
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/test",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer test-token",
        }),
      })
    );
    expect(result).toEqual({ data: "test" });
    vi.unstubAllGlobals();
  });

  it("handles trailing slash in apiUrl", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ok: true }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await apiFetch("/test", {
      apiUrl: "http://localhost:8000/api/v1/",
      token: "token",
      method: "GET",
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/test",
      expect.any(Object)
    );
    vi.unstubAllGlobals();
  });

  it("throws ApiError on non-ok response", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      json: () => Promise.resolve({ error: "FORBIDDEN", message: "Access denied" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(
      apiFetch("/test", { apiUrl: "http://localhost", token: "t", method: "GET" })
    ).rejects.toThrow("Access denied");

    vi.unstubAllGlobals();
  });

  it("returns undefined for 204 No Content", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await apiFetch("/test", {
      apiUrl: "http://localhost",
      token: "t",
      method: "DELETE",
    });
    expect(result).toBeUndefined();
    vi.unstubAllGlobals();
  });
});
