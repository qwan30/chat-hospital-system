import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ContextChip } from "@/components/patient/ContextChip";

describe("ContextChip", () => {
  it("renders patient name and MRN", () => {
    render(<ContextChip fullName="John Doe" mrn="MRN-001" />);
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("MRN: MRN-001")).toBeInTheDocument();
  });

  it("renders initials correctly", () => {
    render(<ContextChip fullName="Sarah Chen" mrn="MRN-002" />);
    expect(screen.getByText("SC")).toBeInTheDocument();
  });

  it("shows denied permission indicator", () => {
    const { container } = render(<ContextChip fullName="John Doe" mrn="MRN-001" permission="denied" />);
    const shield = container.querySelector(".lucide-shield");
    expect(shield).toBeTruthy();
  });
});
