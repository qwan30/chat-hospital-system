/** @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { GraphCanvas } from "./GraphCanvas";

afterEach(cleanup);

describe("GraphCanvas", () => {
  it("keeps stable provenance attributes on visible nodes and edges", () => {
    vi.stubGlobal("requestAnimationFrame", vi.fn());
    render(
      <GraphCanvas
        data={{
          patient_id: "patient-1",
          nodes: [
            {
              id: "node-1",
              type: "diagnosis",
              label: "Diabetes",
              sublabel: "diagnosis",
              source_document_id: "doc-1",
              source_chunk_id: "chunk-1",
              source_start_offset: 10,
              source_end_offset: 20,
              source_bounding_boxes: [0,0,10,10],
              x: 0,
              y: 0,
            },
            {
              id: "node-2",
              type: "medication",
              label: "Metformin",
              source_document_id: "doc-1",
              source_chunk_id: "chunk-2",
              x: 100,
              y: 100,
            },
          ],
          edges: [
            {
              id: "edge-1",
              from_node: "node-1",
              to_node: "node-2",
              label: "treats",
              source_document_id: "doc-1",
              source_chunk_id: "chunk-2",
            },
          ],
          reasoning_path: [],
        }}
      />,
    );

    expect(screen.getByTestId("graph-node-node-1")).toHaveAttribute(
      "data-provenance-document-id",
      "doc-1",
    );
    expect(screen.getByTestId("graph-node-node-1")).toHaveAttribute(
      "data-provenance-chunk-id",
      "chunk-1",
    );
    expect(screen.getByTestId("graph-node-node-1")).toHaveAttribute(
      "data-provenance-start-offset",
      "10",
    );
    expect(screen.getByTestId("graph-node-node-1")).toHaveAttribute(
      "data-provenance-end-offset",
      "20",
    );
    expect(screen.getByTestId("graph-node-node-1")).toHaveAttribute(
      "data-provenance-bounding-boxes",
      "[0,0,10,10]",
    );
    expect(screen.getByTestId("graph-edge-edge-1")).toHaveAttribute(
      "data-provenance-document-id",
      "doc-1",
    );
  });
});
