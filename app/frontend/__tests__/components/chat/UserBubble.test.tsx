import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { UserBubble } from "@/components/chat/UserBubble";

describe("UserBubble", () => {
  it("renders message content", () => {
    render(<UserBubble message="What are the lab results?" />);
    expect(screen.getByText("What are the lab results?")).toBeInTheDocument();
  });

  it("shows timestamp when provided", () => {
    render(<UserBubble message="Hello" timestamp="10:30 AM" />);
    expect(screen.getByText("10:30 AM")).toBeInTheDocument();
  });
});
