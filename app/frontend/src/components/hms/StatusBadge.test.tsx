/** @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

vi.mock("@/lib/utils", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders the mapped label for a known status", () => {
    render(<StatusBadge status="indexed" />);
    expect(screen.getByText("Indexed")).toBeInTheDocument();
  });

  it.each([
    ["ready", "Ready"],
    ["ready_with_warnings", "Ready with warnings"],
  ])("renders a friendly positive label for %s", (status, label) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("prefers an explicit label over the mapped one", () => {
    render(<StatusBadge status="indexed" label="Ready" />);
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.queryByText("Indexed")).not.toBeInTheDocument();
  });

  // Regression: GET /documents returns `ocr_failed`, which had no entry in the
  // status map. Indexing the map returned undefined and reading `.cls` threw,
  // which blanked the entire Documents route with "Something went wrong" -- a
  // crash the API-level tests could not see because the endpoint returns 200.
  it("renders every documents.status value without throwing", () => {
    // The db/models.py:157-158 check constraint, verbatim.
    const documentStatuses = [
      "uploaded",
      "ocr_processing",
      "ocr_failed",
      "ocr_completed",
      "indexing",
      "index_failed",
      "indexed",
      "ready",
      "ready_with_warnings",
      "archived",
    ] as const;
    for (const status of documentStatuses) {
      expect(() => render(<StatusBadge status={status} />)).not.toThrow();
      cleanup();
    }
  });

  it("styles failure states destructively rather than as neutral chrome", () => {
    // dashboard.py:67 counts these two as the `failed` metric, so they must not
    // look like a benign "Uploaded".
    for (const status of ["ocr_failed", "index_failed"] as const) {
      const { container } = render(<StatusBadge status={status} />);
      expect(container.firstChild).toHaveClass("text-destructive");
      cleanup();
    }
  });

  it("falls back to a humanized label for a status outside the known set", () => {
    render(<StatusBadge status="partially-indexed" />);
    expect(screen.getByText("Partially Indexed")).toBeInTheDocument();
  });

  it("still honours an explicit label for an unmapped status", () => {
    render(<StatusBadge status="ocr_failed" label="OCR failed" />);
    expect(screen.getByText("OCR failed")).toBeInTheDocument();
  });
});
