/** @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ClinicalTimelinePanel } from "./ClinicalTimelinePanel";

afterEach(cleanup);

describe("ClinicalTimelinePanel", () => {
  it("keeps conflicting events visible and exposes their provenance", () => {
    render(
      <ClinicalTimelinePanel
        events={[
          {
            event_id: "event-1",
            event_type: "lab",
            clinical_date: "2026-01-02",
            recorded_at: "2026-01-03T10:00:00Z",
            evidence_ids: ["evidence-1"],
            confidence: 0.8,
            reviewer_state: "approved",
            conflict_state: "value_conflict",
            supersession_lineage: ["rev-1", "rev-2"],
            document_id: "doc-1",
            revision_set_id: "set-2",
            page_revision_id: "page-rev-2",
            page: 3,
            alignment_status: "stale",
          },
        ]}
        onSelectEvidence={vi.fn()}
      />,
    );

    expect(screen.getByTestId("timeline-event-event-1")).toBeInTheDocument();
    expect(screen.getByText((_, el) => el?.textContent?.match(/Conflict detected: value conflict/i) !== null)).toBeInTheDocument();
    expect(screen.getByText(/Document: doc-1/i)).toBeInTheDocument();
    expect(screen.getByText(/Revision: set-2/i)).toBeInTheDocument();
    expect(screen.getByText(/Page: 3/i)).toBeInTheDocument();
    expect(screen.getByText(/Geometry stale/i)).toBeInTheDocument();
  });
});
