import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Footer } from "@/components/app-shell/Footer";

describe("Footer", () => {
  it("renders safety disclaimer", () => {
    render(<Footer />);
    expect(screen.getByText(/AI can make mistakes/i)).toBeInTheDocument();
  });
});
