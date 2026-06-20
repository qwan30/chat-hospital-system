/** @vitest-environment jsdom */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("@/lib/utils", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("@tanstack/react-router", async () => {
  const React = await import("react");
  return {
    Link: React.forwardRef<HTMLAnchorElement, Record<string, unknown>>(
      ({ children, to, params, className, ...props }, ref) => {
        let href = String(to ?? "/");
        if (params && typeof params === "object") {
          for (const [key, value] of Object.entries(params)) {
            href = href.replace(`$${key}`, String(value));
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

// ---------------------------------------------------------------------------
// SUT
// ---------------------------------------------------------------------------
import { CitationChip } from "./CitationChip";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("CitationChip", () => {
  it("renders citation number in brackets: [1], [5], etc.", () => {
    render(<CitationChip n={1} sourceId="doc-123" />);
    expect(screen.getByText("[1]")).toBeInTheDocument();
  });

  it("links to the correct citation detail page", () => {
    render(<CitationChip n={5} sourceId="doc-abc" />);
    const link = screen.getByText("[5]");
    expect(link).toHaveAttribute("href", "/documents/doc-abc");
  });

  it("accepts and applies custom className", () => {
    render(<CitationChip n={1} sourceId="doc-123" className="my-custom-class" />);
    const link = screen.getByText("[1]");
    expect(link).toHaveClass("my-custom-class");
  });
});
