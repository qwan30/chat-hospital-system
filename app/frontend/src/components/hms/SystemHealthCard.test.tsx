// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import * as dashboardApi from "@/lib/api/dashboard";
import { SystemHealthCard } from "./SystemHealthCard";

describe("SystemHealthCard", () => {
  it("renders live HMS and LLM health statuses from getDashboardSummary", async () => {
    vi.spyOn(dashboardApi, "getDashboardSummary").mockResolvedValue({
      recent_patients: [],
      document_stats: { indexed: 5, processing: 1, failed: 0 },
      metrics: { hours_saved: 2.5, cost_saved_usd: 150 },
      systems_health: { hms_api: "online", ollama_inference: "degraded" },
    });

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <SystemHealthCard />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/HMS FHIR bridge/i)).toBeTruthy();
      expect(screen.getByText(/online/i)).toBeTruthy();
      expect(screen.getByText(/degraded/i)).toBeTruthy();
    });
  });
});
