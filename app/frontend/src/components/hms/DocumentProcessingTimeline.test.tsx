/** @vitest-environment jsdom */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { DocumentProcessingTimeline } from "./DocumentProcessingTimeline";

vi.mock("@/components/ui/typewriter", () => ({
  TypewriterText: ({ text, className }: { text: string; className?: string }) => (
    <span className={className}>{text}</span>
  ),
}));

describe("DocumentProcessingTimeline", () => {
  it("renders the ordered processing history and identifies a failed stage", () => {
    render(
      <DocumentProcessingTimeline
        events={[
          {
            id: "event-upload",
            attempt: 1,
            sequence: 1,
            stage: "upload",
            state: "completed",
            progress_current: 1,
            progress_total: 1,
            error_code: null,
            created_at: "2026-07-22T08:00:00Z",
          },
          {
            id: "event-ocr",
            attempt: 1,
            sequence: 2,
            stage: "ocr",
            state: "failed",
            progress_current: 2,
            progress_total: 3,
            error_code: "OCR_FAILED",
            created_at: "2026-07-22T08:00:02Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Upload completed")).toBeInTheDocument();
    expect(screen.getByText("OCR failed")).toBeInTheDocument();
    expect(screen.getByText("OCR_FAILED")).toBeInTheDocument();
    expect(screen.getByText("2 / 3")).toBeInTheDocument();
  });
});
