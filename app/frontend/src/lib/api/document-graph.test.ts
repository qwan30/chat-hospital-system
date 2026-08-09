import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api-client", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../api-client";
import { getDocumentGraph } from "./document-graph";

describe("getDocumentGraph", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
  });

  it("calls getDocumentGraph with default filters", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      document_id: "doc-1",
      nodes: [],
      edges: [],
      mentions: [],
      assertions: [],
    });
    await getDocumentGraph("doc-1");
    expect(apiFetch).toHaveBeenCalledWith("/documents/doc-1/graph");
  });

  it("serializes complex graph filters into query parameters", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      document_id: "doc-1",
      nodes: [],
      edges: [],
      mentions: [],
      assertions: [],
    });
    await getDocumentGraph("doc-1", {
      node_limit: 50,
      hop_depth: 2,
      min_confidence: 0.8,
      entity_types: ["medication", "diagnosis"],
      include_superseded: true,
    });
    expect(apiFetch).toHaveBeenCalledWith(expect.stringContaining("/documents/doc-1/graph?"));
    const callArg = vi.mocked(apiFetch).mock.calls[0][0];
    expect(callArg).toContain("node_limit=50");
    expect(callArg).toContain("hop_depth=2");
    expect(callArg).toContain("min_confidence=0.8");
    expect(callArg).toContain("entity_types=medication");
    expect(callArg).toContain("entity_types=diagnosis");
    expect(callArg).toContain("include_superseded=true");
  });
});
