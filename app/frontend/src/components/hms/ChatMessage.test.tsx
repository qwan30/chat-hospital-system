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

vi.mock("lucide-react", async (importOriginal) => {
  const actual = (await importOriginal()) as Record<string, unknown>;
  return {
    ...actual,
    Sparkles: () => null,
    User: () => null,
    Network: () => null,
    ArrowRight: () => null,
  };
});

vi.mock("./CitationChip", async () => {
  const React = await import("react");
  return {
    CitationChip: ({
      n,
      sourceId,
      evidence,
      className,
    }: {
      n?: number;
      sourceId?: string;
      evidence?: { n?: number; sourceId?: string; id?: string; document_id?: string };
      className?: string;
    }) =>
      React.createElement("span", {
        "data-testid": "citation-chip",
        "data-n": String(n ?? evidence?.n ?? 1),
        "data-sourceid":
          sourceId ?? evidence?.sourceId ?? evidence?.document_id ?? evidence?.id ?? "",
        className,
      }),
  };
});

// ---------------------------------------------------------------------------
// SUT
// ---------------------------------------------------------------------------
import { ChatMessage, MarkdownRenderer } from "./ChatMessage";
import type { ChatMessageData } from "./ChatMessage";
import { GraphExplanationPanel } from "./GraphExplanationPanel";

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

describe("MarkdownRenderer & GraphExplanationPanel in ChatMessage", () => {
  it("sanitizes Assistant Markdown and disables executable HTML", () => {
    const unsafeContent = `Hello <script>alert("XSS")</script><img src="x" onerror="alert('XSS')">**bold text**`;
    render(
      <MarkdownRenderer
        content={unsafeContent}
        allowHtml={false}
        allowedProtocols={["http", "https"]}
      />,
    );

    expect(screen.getByText(/bold text/)).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
    const imgs = document.querySelectorAll("img");
    imgs.forEach((img) => expect(img.getAttribute("onerror")).toBeNull());
  });

  it("UI displays 'validated sentence streaming' and never raw token streaming when streaming status or mode is active", () => {
    render(
      <ChatMessage
        msg={msg({
          role: "assistant",
          content: "Generating answer...",
          streamingMode: "validated_sentence_streaming",
          isStreaming: true,
        })}
      />,
    );
    expect(screen.getByText(/validated sentence streaming/i)).toBeInTheDocument();
    expect(screen.queryByText(/token streaming/i)).not.toBeInTheDocument();
  });

  it("renders safe Markdown and graph explanation separately in ChatMessage", () => {
    const explanationData = {
      summary: "Knowledge graph inference path traversed 3 clinical relationships.",
      paths: [
        { from: "Aspirin", relation: "contraindicates", to: "Gastric Ulcer", confidence: 0.94 },
      ],
    };

    render(
      <ChatMessage
        msg={msg({
          role: "assistant",
          content: "Based on patient EHR, Aspirin should be avoided.",
          graphExplanation: explanationData,
        })}
      />,
    );

    expect(
      screen.getByText("Based on patient EHR, Aspirin should be avoided."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Knowledge graph inference path traversed 3 clinical relationships/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/contraindicates/i)).toBeInTheDocument();
  });

  it("MarkdownRenderer supports renderCitation prop for inline citations", () => {
    const renderCitation = vi.fn((id, n) => (
      <span key={id} data-testid="custom-citation">{`[Cit-${n}]`}</span>
    ));
    render(
      <MarkdownRenderer
        content="Evidence found in [doc-1] and [doc-2]."
        allowHtml={false}
        allowedProtocols={["http", "https"]}
        renderCitation={renderCitation}
      />,
    );
    const chips = screen.getAllByTestId("custom-citation");
    expect(chips).toHaveLength(2);
    expect(chips[0]).toHaveTextContent("[Cit-1]");
    expect(chips[1]).toHaveTextContent("[Cit-2]");
  });
});
