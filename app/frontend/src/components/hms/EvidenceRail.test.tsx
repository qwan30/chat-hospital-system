/** @vitest-environment jsdom */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

// Mocks
vi.mock("@/lib/utils", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("@tanstack/react-router", async () => {
  const React = await import("react");
  return {
    Link: React.forwardRef<HTMLAnchorElement, Record<string, unknown>>(
      ({ children, to, params, search, className, ...props }, ref) => {
        let href = String(to ?? "/");
        if (params && typeof params === "object") {
          for (const [key, value] of Object.entries(params)) {
            href = href.replace(`$${key}`, String(value));
          }
        }
        if (search) {
          const searchVal =
            typeof search === "function"
              ? (search as unknown as (prev: Record<string, unknown>) => Record<string, unknown>)(
                  {},
                )
              : search;
          if (searchVal && typeof searchVal === "object" && Object.keys(searchVal).length > 0) {
            const qs = new URLSearchParams(searchVal as Record<string, string>).toString();
            if (qs) href += `?${qs}`;
          }
        }
        return React.createElement(
          "a",
          { ref, className, href, ...props },
          children as React.ReactNode,
        );
      },
    ),
  };
});

import { EvidenceRail, evidenceLabel, type EvidenceItem } from "./EvidenceRail";

describe("EvidenceRail & evidenceLabel", () => {
  it("produces message-stable evidence labels", () => {
    const label = evidenceLabel("msg-alpha", "ev-101", 0);
    expect(label).toEqual({
      stableId: "msg-alpha:ev-101",
      inlineNumber: 1,
      display: "[1]",
    });

    const label2 = evidenceLabel("msg-beta", "ev-202", 2);
    expect(label2).toEqual({
      stableId: "msg-beta:ev-202",
      inlineNumber: 3,
      display: "[3]",
    });
  });

  it("filters and matches numbering to the selected message when selectedMessageId is provided", () => {
    const items: EvidenceItem[] = [
      {
        id: "ev-1",
        n: 1,
        title: "Alpha Study",
        source: "Source 1",
        date: "2026-01-10",
        snippet: "Snippet 1",
        relevance: 0.9,
        document_id: "doc-1",
        messageId: "msg-A",
      },
      {
        id: "ev-2",
        n: 2,
        title: "Beta Report",
        source: "Source 2",
        date: "2026-02-15",
        snippet: "Snippet 2",
        relevance: 0.85,
        document_id: "doc-2",
        messageId: "msg-B",
      },
    ];

    const { rerender } = render(<EvidenceRail items={items} selectedMessageId="msg-B" />);
    expect(screen.getByText("Beta Report")).toBeInTheDocument();
    expect(screen.queryByText("Alpha Study")).not.toBeInTheDocument();
    expect(screen.getByText("[1]")).toBeInTheDocument();

    rerender(<EvidenceRail items={items} />);
    expect(screen.getByText("Alpha Study")).toBeInTheDocument();
    expect(screen.getByText("Beta Report")).toBeInTheDocument();
  });

  it("displays real document date, page, revision, approval state, score, retrieval method, offsets, and aligned geometry status", () => {
    const fullItem: EvidenceItem = {
      id: "ev-full",
      n: 1,
      title: "Comprehensive Clinical Guidelines",
      source: "NEJM 2026",
      date: "2026-05-12",
      snippet: "DAPT duration recommended for 12 months.",
      relevance: 0.95,
      document_id: "doc-guide",
      page: 14,
      revision: "rev-v2.1",
      approvalState: "Approved",
      score: 0.95,
      retrievalMethod: "Dense RAG",
      offsets: "120-240",
      alignedGeometryStatus: "Aligned (page 14 bounding box)",
    };

    render(<EvidenceRail items={[fullItem]} />);

    expect(screen.getByText(/2026-05-12/)).toBeInTheDocument();
    expect(screen.getByText(/Page 14/)).toBeInTheDocument();
    expect(screen.getByText(/rev-v2.1/)).toBeInTheDocument();
    expect(screen.getByText(/Approved/)).toBeInTheDocument();
    expect(screen.getByText(/Dense RAG/)).toBeInTheDocument();
    expect(screen.getByText(/120-240/)).toBeInTheDocument();
    expect(screen.getByText(/Aligned \(page 14 bounding box\)/)).toBeInTheDocument();
  });

  it("exact navigation links include document_id, page, revision, and aligned bounding box", () => {
    const navItem: EvidenceItem = {
      id: "ev-nav",
      n: 1,
      title: "Nav Test Document",
      source: "EHR Notes",
      date: "2026-04-01",
      snippet: "Patient evaluation stable.",
      relevance: 0.88,
      document_id: "doc-nav-123",
      page: 3,
      revision: "rev-7",
      alignedBoundingBox: { x: 10, y: 20, width: 100, height: 50 },
    };

    render(<EvidenceRail items={[navItem]} />);

    const openLink = screen.getByRole("link", { name: /open document/i });
    const href = openLink.getAttribute("href") || "";
    expect(href).toContain("/documents/doc-nav-123");
    expect(href).toContain("page=3");
    expect(href).toContain("revision=rev-7");
    expect(href).toContain("bbox=");
  });
});
