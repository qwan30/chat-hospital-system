import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import * as React from "react";

const mockGetDashboardSummary = vi.fn();

vi.mock("@/lib/api-client", () => ({
  getDashboardSummary: (...args: unknown[]) => mockGetDashboardSummary(...args),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    apiUrl: "http://localhost:1122/api/v1",
    token: "mock-token",
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

import { HospitalDashboard } from "@/components/hospital-dashboard";

describe("HospitalDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading state initially", () => {
    mockGetDashboardSummary.mockReturnValue(new Promise(() => {})); // never resolves
    render(<HospitalDashboard />);
    expect(screen.getByText("Loading workspace summary…")).toBeInTheDocument();
  });

  it("renders error state when BFF call fails", async () => {
    mockGetDashboardSummary.mockRejectedValue(new Error("Connection refused"));
    render(<HospitalDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Error Loading Dashboard")).toBeInTheDocument();
      expect(screen.getByText("Connection refused")).toBeInTheDocument();
    });
  });

  it("renders metrics, health checks and patient list when loaded", async () => {
    mockGetDashboardSummary.mockResolvedValue({
      recent_patients: [
        { id: "patient-1", full_name: "Alice Vance", mrn: "MRN-12345", last_accessed: "2026-06-08T00:00:00Z" }
      ],
      document_stats: { indexed: 42, processing: 2, failed: 1 },
      metrics: { hours_saved: 12.5, cost_saved_usd: 250.75 },
      systems_health: { hms_api: "healthy", ollama_inference: "healthy" }
    });

    render(<HospitalDashboard />);

    await waitFor(() => {
      // Title
      expect(screen.getByText("Hospital Knowledge Assistant")).toBeInTheDocument();
      // Health statuses
      expect(screen.getByText("HMS Connected")).toBeInTheDocument();
      expect(screen.getByText("Ollama Active")).toBeInTheDocument();
      // Metrics
      expect(screen.getByText("12.5 hrs")).toBeInTheDocument();
      expect(screen.getByText("$250.75")).toBeInTheDocument();
      expect(screen.getByText("42 files")).toBeInTheDocument();
      // Recent Patients table
      expect(screen.getByText("Alice Vance")).toBeInTheDocument();
      expect(screen.getByText("MRN: MRN-12345")).toBeInTheDocument();
    });
  });
});
