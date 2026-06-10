import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MedicationList } from "@/components/patient/MedicationList";

const meds = [
  { id: "1", name: "Lisinopril", dosage: "10mg", frequency: "Once daily", route: "PO", indication: "Hypertension", startDate: "Apr 2025", status: "active" },
  { id: "2", name: "Metformin", dosage: "500mg", frequency: "Twice daily", route: "PO", indication: "Diabetes", startDate: "Mar 2025", status: "active" },
];

describe("MedicationList", () => {
  it("renders all medications", () => {
    render(<MedicationList medications={meds} />);
    expect(screen.getByText("Lisinopril")).toBeInTheDocument();
    expect(screen.getByText("Metformin")).toBeInTheDocument();
  });

  it("shows dosage and frequency", () => {
    render(<MedicationList medications={meds} />);
    expect(screen.getByText(/10mg — Once daily — PO/)).toBeInTheDocument();
  });

  it("shows safety concern when present", () => {
    const withConcern = [{ ...meds[0], safetyConcern: "Monitor renal function" }];
    render(<MedicationList medications={withConcern} />);
    expect(screen.getByText("Monitor renal function")).toBeInTheDocument();
  });
});
