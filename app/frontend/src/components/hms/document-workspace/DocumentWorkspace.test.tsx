/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DocumentWorkspace } from "./DocumentWorkspace";
import { GeometryOverlay } from "./GeometryOverlay";
import { restoreRevision } from "@/lib/api/document-revisions";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom/vitest";

vi.mock("@/lib/api/document-revisions", () => ({
  restoreRevision: vi.fn(),
  listRevisionSets: vi.fn().mockResolvedValue([
    { revision_set_id: "rev-1", revision_number: 1, status: "approved" },
  ]),
}));

vi.mock("@/lib/api/documents", () => ({
  getDocument: vi.fn().mockResolvedValue({ id: "doc-1", mime_type: "application/pdf" }),
  getDocumentBlob: vi.fn().mockResolvedValue(new Blob(["mock"], { type: "application/pdf" })),
}));

// Mock URL.createObjectURL since it's not in jsdom
beforeEach(() => {
  URL.createObjectURL = vi.fn().mockReturnValue("blob:mock");
  URL.revokeObjectURL = vi.fn();
});

const queryClient = new QueryClient();

describe("DocumentWorkspace", () => {
  it("keeps a historical revision read-only and restores as a new child", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DocumentWorkspace documentId="doc-1" />
      </QueryClientProvider>
    );

    // Wait for the revision to load in the selector
    const selector = await screen.findByRole("combobox", { name: /revision/i });
    fireEvent.change(selector, { target: { value: "rev-1" } });

    // Since it's a historical revision, we should see the diff instead of the editor
    expect(await screen.findByText("Revision Differences")).toBeInTheDocument();
    
    // Check that we can restore
    const restoreBtn = screen.getByRole("button", { name: "Restore as new revision" });
    fireEvent.click(restoreBtn);
    
    await waitFor(() => {
      expect(restoreRevision).toHaveBeenCalledWith("doc-1", "rev-1", expect.any(Object), expect.any(Object));
    });
  });
});

describe("GeometryOverlay", () => {
  it("renders exact boxes but shows alert for stale ones", () => {
    const boxes = [
      { id: "box-1", top: 0, left: 0, width: 0.1, height: 0.1, alignment_status: "aligned" }
    ];
    render(<GeometryOverlay boxes={boxes} staleCount={2} />);
    
    // Exact box rendered
    const exactBox = document.querySelector(".border-primary");
    expect(exactBox).toBeInTheDocument();
    
    // Alert for stale count
    expect(screen.getByText(/2 annotations are stale/i)).toBeInTheDocument();
  });
});
