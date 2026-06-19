/** @vitest-environment jsdom */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

afterEach(cleanup);

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("@/lib/utils", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("lucide-react", () => ({
  AlertTriangle: () => null,
  Loader2: () => null,
  Play: () => null,
  RotateCcw: () => null,
  Square: () => null,
}));

vi.mock("@/components/ui/button", async () => {
  const React = await import("react");
  return {
    Button: React.forwardRef<HTMLButtonElement, Record<string, unknown>>(
      ({ children, ...props }, ref) =>
        React.createElement("button", { ref, ...props }, children as React.ReactNode),
    ),
  };
});

// ---------------------------------------------------------------------------
// SUT
// ---------------------------------------------------------------------------
import { StreamingControls } from "./StreamingControls";

// ---------------------------------------------------------------------------
// Shared stub callbacks
// ---------------------------------------------------------------------------
const noop = () => {};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("StreamingControls", () => {
  it("returns null when status is idle", () => {
    const { container } = render(
      <StreamingControls
        status="idle"
        progress={0}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={noop}
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("returns null when status is complete", () => {
    const { container } = render(
      <StreamingControls
        status="complete"
        progress={100}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={noop}
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it('shows "Streaming... N%" with Stop button when streaming', () => {
    render(
      <StreamingControls
        status="streaming"
        progress={37}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={noop}
      />,
    );
    expect(screen.getByText(/Streaming.*37%/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /stop/i })).toBeInTheDocument();
  });

  it("shows interrupted response banner with Resume and Retry buttons", () => {
    render(
      <StreamingControls
        status="interrupted"
        progress={55}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={noop}
      />,
    );
    expect(screen.getByText(/interrupted.*55%/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /resume/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("shows custom error message in interrupted banner", () => {
    render(
      <StreamingControls
        status="interrupted"
        error="Custom network error"
        progress={42}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={noop}
      />,
    );
    expect(screen.getByText("Custom network error")).toBeInTheDocument();
  });

  it("displays default fallback error when no error provided", () => {
    render(
      <StreamingControls
        status="interrupted"
        progress={0}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={noop}
      />,
    );
    expect(screen.getByText("The stream ended unexpectedly.")).toBeInTheDocument();
  });

  it("calls onStop when Stop button is clicked", () => {
    const onStop = vi.fn();
    render(
      <StreamingControls
        status="streaming"
        progress={50}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={onStop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /stop/i }));
    expect(onStop).toHaveBeenCalledTimes(1);
  });

  it("calls onRetry when 'Retry from start' is clicked", () => {
    const onRetry = vi.fn();
    render(
      <StreamingControls
        status="interrupted"
        progress={50}
        total={100}
        onRetry={onRetry}
        onResume={noop}
        onStop={noop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("calls onResume when Resume button is clicked", () => {
    const onResume = vi.fn();
    render(
      <StreamingControls
        status="interrupted"
        progress={50}
        total={100}
        onRetry={noop}
        onResume={onResume}
        onStop={noop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /resume/i }));
    expect(onResume).toHaveBeenCalledTimes(1);
  });

  it("uses custom resumeLabel when provided", () => {
    render(
      <StreamingControls
        status="interrupted"
        progress={50}
        total={100}
        onRetry={noop}
        onResume={noop}
        onStop={noop}
        resumeLabel="Continue generating"
      />,
    );
    expect(screen.getByRole("button", { name: /continue generating/i })).toBeInTheDocument();
  });
});
