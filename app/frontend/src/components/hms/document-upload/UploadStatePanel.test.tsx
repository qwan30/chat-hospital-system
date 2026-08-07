/** @vitest-environment jsdom */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { UploadStatePanel, type UploadUiState } from "./UploadStatePanel";
import "@testing-library/jest-dom/vitest";

describe("UploadStatePanel", () => {
  it.each([
    ["pending", "Pending verification..."],
    ["uploaded_unverified", "Verifying upload..."],
    ["verified", "Upload verified"],
    ["finalized", "Upload finalized"],
    ["quarantined", "Upload quarantined"],
    ["rejected", "Upload rejected"],
  ] as const)("renders the %s lifecycle state", (kind, label) => {
    const state: UploadUiState = { kind };

    render(<UploadStatePanel state={state} onReset={vi.fn()} />);

    expect(screen.getByText(label)).toBeInTheDocument();
  });
});
