import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DetailHeader } from "@/components/patient/DetailHeader";

describe("DetailHeader", () => {
  it("renders patient name and MRN", () => {
    render(<DetailHeader fullName="Jane Smith" mrn="MRN-100" />);
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.getByText(/MRN: MRN-100/)).toBeInTheDocument();
  });

  it("shows status badge", () => {
    render(<DetailHeader fullName="Jane Smith" mrn="MRN-100" status="admitted" />);
    expect(screen.getByText("Admitted")).toBeInTheDocument();
  });

  it("renders with optional fields", () => {
    render(<DetailHeader fullName="Jane Smith" mrn="MRN-100" dob="1990-01-15" gender="Female" department="Cardiology" />);
    expect(screen.getByText(/DOB: 1990-01-15/)).toBeInTheDocument();
    expect(screen.getByText("Female")).toBeInTheDocument();
    expect(screen.getByText("Cardiology")).toBeInTheDocument();
  });
});
