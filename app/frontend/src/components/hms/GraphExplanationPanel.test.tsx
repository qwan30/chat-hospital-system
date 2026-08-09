/** @vitest-environment jsdom */
import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { GraphExplanationPanel } from "./GraphExplanationPanel";

afterEach(cleanup);

describe("GraphExplanationPanel", () => {
  it("renders scalar path provenance without treating stale geometry as exact", () => {
    render(
      <GraphExplanationPanel
        explanation={{
          summary: "A source-backed path",
          paths: [
            {
              from: "Diabetes",
              relation: "treated_by",
              to: "Metformin",
              document_id: "doc-1",
              revision_set_id: "set-1",
              page_revision_id: "page-rev-1",
              page: 2,
              alignment_status: "stale",
            },
          ],
        }}
      />,
    );

    expect(screen.getByText(/Document: doc-1/i)).toBeInTheDocument();
    expect(screen.getByText(/Revision: set-1/i)).toBeInTheDocument();
    expect(screen.getByText(/Page: 2/i)).toBeInTheDocument();
    expect(screen.getByText(/Geometry stale/i)).toBeInTheDocument();
    expect(screen.queryByText(/Exact evidence locator/i)).not.toBeInTheDocument();
  });
});
