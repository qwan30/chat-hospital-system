/** @vitest-environment jsdom */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import type { ReactNode } from "react";

afterEach(cleanup);

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("@/lib/utils", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("lucide-react", () => ({
  Sparkles: () => null,
  User: () => null,
}));

vi.mock("./CitationChip", async () => {
  const React = await import("react");
  return {
    CitationChip: ({
      n,
      sourceId,
      className,
    }: {
      n: number;
      sourceId: string;
      className?: string;
    }) =>
      React.createElement("span", {
        "data-testid": "citation-chip",
        "data-n": String(n),
        "data-sourceid": sourceId,
        className,
      }),
  };
});

// ---------------------------------------------------------------------------
// SUT
// ---------------------------------------------------------------------------
import { ChatMessage } from "./ChatMessage";
import type { ChatMessageData } from "./ChatMessage";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function msg(
  overrides: Partial<ChatMessageData> & { role: "user" | "assistant" },
): ChatMessageData {
  return {
    id: "test-id",
    content: "",
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("ChatMessage", () => {
  it("renders user message with 'You' label and content", () => {
    render(<ChatMessage msg={msg({ role: "user", content: "Hello there" })} />);
    expect(screen.getByText("You")).toBeInTheDocument();
    expect(screen.getByText("Hello there")).toBeInTheDocument();
  });

  it("renders assistant message with 'HMS Copilot' label", () => {
    render(<ChatMessage msg={msg({ role: "assistant", content: "Hi, how can I help?" })} />);
    expect(screen.getByText("HMS Copilot")).toBeInTheDocument();
    expect(screen.getByText("Hi, how can I help?")).toBeInTheDocument();
  });

  it("sets data-msg-role attribute correctly for user and assistant", () => {
    const { container, rerender } = render(
      <ChatMessage msg={msg({ role: "user", content: "Hi" })} />,
    );
    const msgEl = container.querySelector("[data-msg-role]");
    expect(msgEl).toHaveAttribute("data-msg-role", "user");

    rerender(<ChatMessage msg={msg({ role: "assistant", content: "Hi" })} />);
    const msgEl2 = container.querySelector("[data-msg-role]");
    expect(msgEl2).toHaveAttribute("data-msg-role", "assistant");
  });

  it("renders time when provided", () => {
    render(<ChatMessage msg={msg({ role: "user", content: "Hi", time: "10:30 AM" })} />);
    // The time is rendered with a middle-dot prefix: "· 10:30 AM"
    expect(screen.getByText(/10:30 AM/)).toBeInTheDocument();
  });

  it("renders inline citation chips when citations are present in content", () => {
    render(
      <ChatMessage
        msg={msg({
          role: "assistant",
          content: "See [1] and [2] for details.",
          citations: [
            { n: 1, sourceId: "doc-alpha" },
            { n: 2, sourceId: "doc-beta" },
          ],
        })}
      />,
    );
    // Text around citations should still render
    expect(screen.getByText("See")).toBeInTheDocument();
    expect(screen.getByText("and")).toBeInTheDocument();
    expect(screen.getByText("for details.")).toBeInTheDocument();

    // Citation chips should be rendered
    const chips = screen.getAllByTestId("citation-chip");
    expect(chips).toHaveLength(2);
    expect(chips[0]).toHaveAttribute("data-n", "1");
    expect(chips[0]).toHaveAttribute("data-sourceid", "doc-alpha");
    expect(chips[1]).toHaveAttribute("data-n", "2");
    expect(chips[1]).toHaveAttribute("data-sourceid", "doc-beta");
  });

  it("renders extra content (ReactNode) when provided", () => {
    const extra: ReactNode = <button type="button">Extra Action</button>;
    render(<ChatMessage msg={msg({ role: "assistant", content: "Result", extra })} />);
    expect(screen.getByRole("button", { name: "Extra Action" })).toBeInTheDocument();
  });
});
