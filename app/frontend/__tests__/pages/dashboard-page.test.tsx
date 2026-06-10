import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "@/app/(app)/dashboard/page";

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ apiUrl: "http://localhost", token: "test-token", isAuthenticated: true }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api-client", () => ({
  getDashboardSummary: vi.fn().mockResolvedValue({
    recent_patients: [{ id: "1", full_name: "John Doe", mrn: "MRN-001" }],
    document_stats: { indexed: 10, processing: 2, failed: 1 },
    metrics: { hours_saved: 120, cost_saved_usd: 15000 },
    systems_health: { hms_api: "ok", ollama_inference: "ok" },
  }),
}));

describe("DashboardPage", () => {
  it("renders dashboard heading after data loads", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("shows KPI metrics after loading", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("120h")).toBeInTheDocument();
    });
  });
});
