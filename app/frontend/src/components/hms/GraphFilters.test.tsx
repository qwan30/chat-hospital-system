/** @vitest-environment jsdom */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

if (typeof global.ResizeObserver === "undefined") {
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}

import { GraphFilters, DEFAULT_GRAPH_FILTERS, serializeGraphFilters } from "./GraphFilters";

describe("GraphFilters", () => {
  it("defines DEFAULT_GRAPH_FILTERS matching specification", () => {
    expect(DEFAULT_GRAPH_FILTERS).toEqual({
      node_limit: 50,
      edge_limit: 100,
      hop_depth: 2,
      entity_types: [],
      relation_types: [],
      min_confidence: 0,
      document_scope: [],
      layout: "force",
      include_superseded: false,
    });
  });

  it("serializes graph filters to URLSearchParams properly", () => {
    const params = serializeGraphFilters({
      ...DEFAULT_GRAPH_FILTERS,
      node_limit: 25,
      include_superseded: true,
    });
    expect(params.get("node_limit")).toBe("25");
    expect(params.get("include_superseded")).toBe("true");
    expect(params.get("layout")).toBe("force");
  });

  it("does not show include_superseded toggle when capability is not granted", () => {
    const onChange = vi.fn();
    render(
      <GraphFilters
        filters={DEFAULT_GRAPH_FILTERS}
        onChange={onChange}
        capabilities={["basic.read"]}
      />,
    );
    expect(screen.queryByLabelText(/include superseded/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/include superseded/i)).not.toBeInTheDocument();
  });

  it("shows include_superseded toggle when superseded_evidence.read capability is granted and labels rows correctly", () => {
    const onChange = vi.fn();
    const supersededItems = [
      { id: "sup-1", label: "Old Aspirin recommendation", text: "81mg daily (outdated)" },
    ];

    const { rerender } = render(
      <GraphFilters
        filters={DEFAULT_GRAPH_FILTERS}
        onChange={onChange}
        capabilities={["superseded_evidence.read"]}
        supersededEvidenceList={supersededItems}
      />,
    );

    const toggle = screen.getByLabelText(/include superseded/i);
    expect(toggle).toBeInTheDocument();

    // When filters have include_superseded: true, display audit-only label
    rerender(
      <GraphFilters
        filters={{ ...DEFAULT_GRAPH_FILTERS, include_superseded: true }}
        onChange={onChange}
        capabilities={["superseded_evidence.read"]}
        supersededEvidenceList={supersededItems}
      />,
    );

    expect(screen.getByText(/Audit-only superseded evidence/i)).toBeInTheDocument();
    expect(screen.getByText("Old Aspirin recommendation")).toBeInTheDocument();
  });

  it("shows source-backed paths separately from final citations", () => {
    const sourcePaths = [
      { id: "path-1", path: ["Patient", "Encounter", "Diagnosis"], source: "Doc A, Page 1" },
    ];
    const citations = [{ id: "cit-1", title: "Clinical Guidelines", source: "Doc B, Page 5" }];

    render(
      <GraphFilters
        filters={DEFAULT_GRAPH_FILTERS}
        onChange={vi.fn()}
        sourceBackedPaths={sourcePaths}
        finalCitations={citations}
      />,
    );

    expect(screen.getByText(/Source-backed paths/i)).toBeInTheDocument();
    expect(screen.getByText(/Final citations/i)).toBeInTheDocument();
    expect(screen.getByText(/Doc A, Page 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Clinical Guidelines/i)).toBeInTheDocument();
  });

  it("does not render controls that the connected route does not support", () => {
    render(
      <GraphFilters
        filters={DEFAULT_GRAPH_FILTERS}
        onChange={vi.fn()}
        supportedFilters={["node_limit", "edge_limit", "layout"]}
      />,
    );

    expect(screen.getByLabelText("Node Limit")).toBeInTheDocument();
    expect(screen.getByLabelText("Edge Limit")).toBeInTheDocument();
    expect(screen.queryByLabelText("Hop Depth")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Minimum Confidence")).not.toBeInTheDocument();
  });
});
