import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CitationCard } from "@/components/evidence/CitationCard";

describe("CitationCard", () => {
  it("renders document title and page", () => {
    render(
      <CitationCard id={1} documentTitle="Admission Note" page={2} snippet="Patient presented with chest pain" confidence={0.92} />
    );
    expect(screen.getByText("Admission Note")).toBeInTheDocument();
    expect(screen.getByText(/Page 2/)).toBeInTheDocument();
  });

  it("shows confidence percentage", () => {
    render(
      <CitationCard id={1} documentTitle="Note" page={1} snippet="text" confidence={0.85} />
    );
    expect(screen.getByText("85%")).toBeInTheDocument();
  });
});
