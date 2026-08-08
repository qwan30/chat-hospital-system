/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DocumentWorkspace } from "./DocumentWorkspace";
import { GeometryOverlay } from "./GeometryOverlay";
import {
  restoreRevision,
  getRevisionPage,
  getDraftPage,
  listRevisionSets,
  submitDraft,
} from "@/lib/api/document-revisions";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom/vitest";

vi.mock("@/lib/api/document-revisions", () => ({
  restoreRevision: vi.fn(),
  getRevisionPage: vi.fn().mockResolvedValue({
    page_revision_id: "page-revision-1",
    lock_version: 7,
    page_number: 1,
    text: "historical",
    status: "approved",
  }),
  getDraftPage: vi.fn().mockResolvedValue({
    page_revision_id: "draft-page-revision-1",
    lock_version: 3,
    page_number: 1,
    text: "draft",
    status: "draft",
  }),
  submitDraft: vi.fn(),
  listRevisionSets: vi
    .fn()
    .mockResolvedValue([{ revision_set_id: "rev-1", revision_number: 1, status: "approved" }]),
}));

vi.mock("@/lib/api/documents", () => ({
  getDocument: vi.fn().mockResolvedValue({ id: "doc-1", mime_type: "application/pdf" }),
  getDocumentBlob: vi.fn().mockResolvedValue(new Blob(["mock"], { type: "application/pdf" })),
  getDocumentPage: vi.fn().mockResolvedValue({
    id: "page-1",
    document_id: "doc-1",
    page_number: 1,
    ocr_text: "test text",
  }),
  getDocumentFacts: vi.fn().mockResolvedValue({ document_id: "doc-1", facts: [] }),
}));

// Mock URL.createObjectURL since it's not in jsdom
beforeEach(() => {
  URL.createObjectURL = vi.fn().mockReturnValue("blob:mock");
  URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  cleanup();
});

const queryClient = new QueryClient();

describe("DocumentWorkspace", () => {
  it("keeps a historical revision read-only and restores as a new child", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DocumentWorkspace documentId="doc-1" />
      </QueryClientProvider>,
    );

    // Wait for the revision to load in the selector
    const selector = await screen.findByRole("combobox", { name: /revision/i });
    await screen.findByRole("option", { name: "rev-1" });
    fireEvent.change(selector, { target: { value: "rev-1" } });

    // Wait for the revision UI to switch to historical view
    const restoreBtn = await screen.findByRole("button", { name: "Restore as new revision" });
    await waitFor(() => expect(getRevisionPage).toHaveBeenCalled());
    fireEvent.click(restoreBtn);

    await waitFor(() => {
      expect(restoreRevision).toHaveBeenCalledWith(
        "doc-1",
        "rev-1",
        { revision_id: "page-revision-1" },
        expect.any(Object),
      );
    });
  });

  it("submits the loaded draft with its current lock version", async () => {
    vi.mocked(submitDraft).mockResolvedValue({
      revision_set_id: "set-1",
      document_id: "doc-1",
      revision_number: 2,
      status: "submitted",
      created_by_user_id: "user-1",
      created_at: null,
      submitted_at: null,
      approved_by_user_id: null,
      approved_at: null,
    });
    render(
      <QueryClientProvider client={new QueryClient()}>
        <DocumentWorkspace documentId="doc-1" />
      </QueryClientProvider>,
    );

    const submit = await screen.findByRole("button", { name: "Submit Draft" });
    await waitFor(() => expect(submit).not.toBeDisabled());
    fireEvent.click(submit);

    await waitFor(() => {
      expect(submitDraft).toHaveBeenCalledWith(
        "doc-1",
        expect.objectContaining({ lockVersion: 3 }),
      );
    });
  });

  it("selects a submitted revision when reopening a document for approval", async () => {
    vi.mocked(listRevisionSets).mockResolvedValueOnce([
      {
        revision_set_id: "submitted-set",
        revision_number: 2,
        status: "submitted",
        created_by_user_id: "doctor-1",
        created_at: null,
        submitted_at: null,
        approved_by_user_id: null,
        approved_at: null,
        document_id: "doc-1",
      },
    ]);

    render(
      <QueryClientProvider client={new QueryClient()}>
        <DocumentWorkspace documentId="doc-1" />
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("button", { name: "Approve" })).toBeVisible();
  });
});

describe("GeometryOverlay", () => {
  it("renders exact boxes but shows alert for stale ones", () => {
    const boxes = [
      { id: "box-1", top: 0, left: 0, width: 0.1, height: 0.1, alignment_status: "aligned" },
    ];
    render(<GeometryOverlay boxes={boxes} staleCount={2} />);

    // Exact box rendered
    const exactBox = document.querySelector(".border-primary");
    expect(exactBox).toBeInTheDocument();

    // Alert for stale count
    expect(screen.getByText(/2 annotations are stale/i)).toBeInTheDocument();
  });
});
