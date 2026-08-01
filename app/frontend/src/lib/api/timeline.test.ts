import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api-client", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../api-client";
import { getGlobalTimeline } from "./timeline";

describe("getGlobalTimeline", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
  });

  it("passes a client-relative endpoint to apiFetch", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ events: [], total_count: 0 });

    await getGlobalTimeline();

    expect(apiFetch).toHaveBeenCalledWith("/timeline?limit=50&offset=0");
  });

  it("preserves explicit pagination values", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ events: [], total_count: 0 });

    await getGlobalTimeline(10, 20);

    expect(apiFetch).toHaveBeenCalledWith("/timeline?limit=10&offset=20");
  });
});
