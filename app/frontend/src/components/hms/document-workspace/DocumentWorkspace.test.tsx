/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { DocumentWorkspace } from "./DocumentWorkspace";
import { GeometryOverlay } from "./GeometryOverlay";
import {
  restoreRevision,
  getRevisionPage,
  getDraftPage,
  listRevisionSets,
  saveDraftPage,
  submitDraft,
} from "@/lib/api/document-revisions";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom/vitest";

vi.mock("@/lib/api/document-revisions", () => ({
  saveDraftPage: vi.fn(),
  restoreRevision: vi.fn(),
  submitDraft: vi.fn(),
  approveRevisionSet: vi.fn(),
  getDraftPage: vi.fn().mockResolvedValue({
    page_revision_id: "draft-page-1",
    lock_version: 1,
    page_number: 1,
    text: "draft text",
    status: "draft",
  }),
  getRevisionPage: vi.fn().mockResolvedValue({
    page_revision_id: "revision-page-1",
    lock_version: 1,
    page_number: 1,
    text: "historical text",
    status: "approved",
  }),
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

const queryClient = new QueryClient();

afterEach(() => {
  cleanup();
  queryClient.clear();
  vi.clearAllMocks();
});

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
    fireEvent.click(restoreBtn);

    await waitFor(() => {
      expect(restoreRevision).toHaveBeenCalledWith(
        "doc-1",
        "rev-1",
        expect.any(Object),
        expect.any(Object),
      );
    });
  });

  it("submits with the lock version returned by saving the draft", async () => {
    vi.mocked(listRevisionSets).mockResolvedValueOnce([]);
    vi.mocked(saveDraftPage).mockResolvedValue({
      page_revision_id: "draft-page-revision-2",
      lock_version: 4,
      page_number: 1,
      text: "saved draft",
      status: "draft",
    });
    vi.mocked(submitDraft).mockResolvedValue({
      revision_set_id: "set-2",
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

    const editor = await screen.findByRole("textbox", { name: "Corrected page text" });
    const submitButton = screen.getByRole("button", { name: "Submit Draft" });
    // The toolbar is enabled only after the revision-page query has loaded its lock version.
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.change(editor, { target: { value: "saved draft" } });
    fireEvent.change(screen.getByPlaceholderText("Edit reason"), {
      target: { value: "corrected text" },
    });
    const saveButton = screen.getByRole("button", { name: "Save draft" });
    await waitFor(() => expect(saveButton).not.toBeDisabled());
    fireEvent.click(saveButton);

    await waitFor(() => expect(saveDraftPage).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByPlaceholderText("Edit reason")).toHaveValue(""));
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitDraft).toHaveBeenCalledWith(
        "doc-1",
        expect.objectContaining({ lockVersion: 4 }),
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

  it("submits the draft with the current lock version", async () => {
    vi.mocked(submitDraft).mockResolvedValueOnce({
      revision_set_id: "submitted-set",
      document_id: "doc-1",
      revision_number: 2,
      status: "submitted",
      created_by_user_id: "doctor-1",
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

    const submitButton = await screen.findByRole("button", { name: "Submit Draft" });
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitDraft).toHaveBeenCalledWith("doc-1", {
        idempotencyKey: expect.any(String),
        lockVersion: 1,
      });
    });
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
