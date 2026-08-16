/** @vitest-environment jsdom */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

if (typeof global.ResizeObserver === "undefined") {
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}

import { RevisionDiff } from "./RevisionDiff";

const LAB_PAGE = [
  "Ho Dinh Dat, Glucose, 107.0, mg/dL",
  "Ho Dinh Dat, HbA1c, 6.5, %",
  "Ho Dinh Dat, Potassium, 4.4, mmol/L",
].join("\n");

describe("RevisionDiff", () => {
  it("shows additions and deletions badges with counts", () => {
    render(
      <RevisionDiff
        originalText={"alpha\nbeta\ngamma"}
        correctedText={"alpha\ngamma\ndelta\nepsilon"}
      />,
    );

    expect(screen.getByText("+2 additions")).toBeInTheDocument();
    expect(screen.getByText("\u22121 deletion")).toBeInTheDocument();
    expect(screen.queryByText(/modification/)).not.toBeInTheDocument();
  });

  it("highlights the changed value inside a modified lab line", () => {
    render(
      <RevisionDiff originalText={LAB_PAGE} correctedText={LAB_PAGE.replace("107.0", "104.0")} />,
    );

    expect(document.querySelector('[data-diff="removed-word"]')?.textContent).toBe("107.0");
    expect(document.querySelector('[data-diff="added-word"]')?.textContent).toBe("104.0");
  });

  it("toggles to unified view with removed and added markers", () => {
    render(<RevisionDiff originalText={LAB_PAGE} correctedText={LAB_PAGE.replace("6.5", "6.3")} />);

    fireEvent.click(screen.getByRole("button", { name: "Unified" }));

    expect(screen.getByText("Unified diff")).toBeInTheDocument();
    expect(document.querySelector('[data-diff-marker="\u2212"]')).toBeInTheDocument();
    expect(document.querySelector('[data-diff-marker="+"]')).toBeInTheDocument();
  });

  it("shows a match state when the corrected text is identical to the original", () => {
    render(<RevisionDiff originalText={LAB_PAGE} correctedText={LAB_PAGE} />);

    expect(screen.getByText("Corrected text matches the original")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Next change" })).not.toBeInTheDocument();
    expect(screen.getByText("100% match")).toBeInTheDocument();
  });

  it("flags unsaved edits in the summary bar", () => {
    render(
      <RevisionDiff
        originalText={LAB_PAGE}
        correctedText={LAB_PAGE.replace("107.0", "104.0")}
        hasUnsavedEdits
      />,
    );

    expect(screen.getByText("Unsaved edits included")).toBeInTheDocument();
  });

  it("navigates between change blocks and updates the counter", () => {
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;

    render(
      <RevisionDiff
        originalText={"alpha\nbeta\ngamma\ndelta"}
        correctedText={"alpha\nBETA\ngamma\nDELTA"}
      />,
    );

    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next change" }));
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
    expect(scrollIntoView).toHaveBeenCalled();
  });
});
