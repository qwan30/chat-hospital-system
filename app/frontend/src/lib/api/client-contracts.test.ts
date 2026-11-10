import { beforeEach, describe, expect, it, vi } from "vitest";
import * as apiClient from "../api-client";
import { getVectorMetrics } from "./metrics";
import { login } from "./auth";
import { sendMessage } from "./chat";

describe("Frontend API client contracts", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls /metrics/vector without duplicate /api/v1 prefix", async () => {
    const spy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      indexed_document_count: 1,
      active_chunk_count: 2,
      sources: [],
    });
    await getVectorMetrics();
    expect(spy).toHaveBeenCalledWith("/metrics/vector");
  });

  it("sends OAuth2 form-urlencoded username and password in login()", async () => {
    const spy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      access_token: "tok",
      token_type: "bearer",
      user: { id: "1", email: "doctor@example.test", full_name: "Doc", role: "cardiologist", is_active: true },
    });
    await login("doctor@example.test", "demo");
    expect(spy).toHaveBeenCalledWith("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "username=doctor%40example.test&password=demo",
    });
  });

  it("maps message to question and nests document_ids inside context in sendMessage()", async () => {
    const spy = vi.spyOn(apiClient, "apiFetch").mockResolvedValue({
      answer: "ok",
      thread_id: "t1",
      citations: [],
    });
    await sendMessage({
      message: "Check labs",
      patient_id: "p1",
      document_ids: ["d1", "d2"],
      thread_id: "t1",
    });
    expect(spy).toHaveBeenCalledWith("/chat", {
      method: "POST",
      body: JSON.stringify({
        question: "Check labs",
        patient_id: "p1",
        thread_id: "t1",
        context: { patient_id: "p1", document_ids: ["d1", "d2"] },
      }),
    });
  });
});
