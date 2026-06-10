import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SafeRefusalCard } from "@/components/chat/SafeRefusalCard";

describe("SafeRefusalCard", () => {
  it("renders refusal reason", () => {
    render(<SafeRefusalCard reason="Insufficient evidence available" />);
    expect(screen.getByText("Cannot answer this question")).toBeInTheDocument();
    expect(screen.getByText("Insufficient evidence available")).toBeInTheDocument();
  });

  it("renders suggestions", () => {
    render(<SafeRefusalCard reason="No data" suggestions={["Try rephrasing", "Check documents"]} />);
    expect(screen.getByText("Try rephrasing")).toBeInTheDocument();
    expect(screen.getByText("Check documents")).toBeInTheDocument();
  });
});
