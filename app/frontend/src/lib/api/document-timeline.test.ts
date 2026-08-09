import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api-client", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../api-client";
import { getDocumentTimeline } from "./document-timeline";

describe("getDocumentTimeline", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
  });

  it("calls getDocumentTimeline with document_id", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ document_id: "doc-1", events: [] });
    await getDocumentTimeline("doc-1");
    expect(apiFetch).toHaveBeenCalledWith("/documents/doc-1/timeline");
  });

  it("passes only filters supported by the document timeline contract", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ document_id: "doc-1", events: [] });
    await getDocumentTimeline("doc-1", {
      date_from: "2026-01-01",
      date_to: "2026-01-31",
      min_confidence: 0.8,
    });
    const callArg = vi.mocked(apiFetch).mock.calls[0][0];
    expect(callArg).toContain("date_from=2026-01-01");
    expect(callArg).toContain("date_to=2026-01-31");
    expect(callArg).toContain("min_confidence=0.8");
    expect(callArg).not.toContain("revision=");
    expect(callArg).not.toContain("include_superseded=");
  });
});
