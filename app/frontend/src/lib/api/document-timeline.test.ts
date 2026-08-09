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

  it("passes timeline filter query parameters", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ document_id: "doc-1", events: [] });
    await getDocumentTimeline("doc-1", {
      revision: "set-2",
      date_from: "2026-01-01",
      event_types: ["chat", "audit"],
      include_superseded: true,
    });
    const callArg = vi.mocked(apiFetch).mock.calls[0][0];
    expect(callArg).toContain("revision=set-2");
    expect(callArg).toContain("date_from=2026-01-01");
    expect(callArg).toContain("event_types=chat");
    expect(callArg).toContain("event_types=audit");
    expect(callArg).toContain("include_superseded=true");
  });
});
