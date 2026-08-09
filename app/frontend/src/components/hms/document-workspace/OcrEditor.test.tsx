/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OcrEditor } from "./OcrEditor";
import { saveDraftPage } from "@/lib/api/document-revisions";
import { ApiError } from "@/lib/api-client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom/vitest";

vi.mock("@/lib/api/document-revisions", () => ({
  saveDraftPage: vi.fn(),
}));

const queryClient = new QueryClient();

afterEach(() => {
  cleanup();
  queryClient.clear();
  vi.clearAllMocks();
});

describe("OcrEditor", () => {
  it("shows a compare action on stale If-Match without losing local text", async () => {
    const user = userEvent.setup();
    vi.mocked(saveDraftPage).mockRejectedValue(new ApiError(409, "CONFLICT", "Draft changed"));

    render(
      <QueryClientProvider client={queryClient}>
        <OcrEditor
          documentId="doc-1"
          page={1}
          initialText="local correction"
          lockVersion={3}
          parentRevisionId="rev-1"
          revision={{ id: "rev-1", text: "old text", status: "draft" }}
        />
      </QueryClientProvider>,
    );

    await user.type(screen.getByPlaceholderText("Edit reason"), "fixed a typo");
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    expect(saveDraftPage).toHaveBeenCalledWith(
      "doc-1",
      1,
      { text: "local correction", parent_revision_id: "rev-1", edit_reason: "fixed a typo" },
      { idempotencyKey: expect.any(String), lockVersion: 3 },
    );
    expect(screen.getByDisplayValue("local correction")).toBeVisible();
    expect(screen.getByRole("button", { name: "Compare with latest" })).toBeVisible();
  });

  it("updates the lock version after a successful draft save", async () => {
    const user = userEvent.setup();
    const onLockVersionChange = vi.fn();
    vi.mocked(saveDraftPage).mockResolvedValue({
      page_revision_id: "rev-2",
      lock_version: 4,
      page_number: 1,
      text: "updated text",
      status: "human_draft",
    });

    render(
      <QueryClientProvider client={new QueryClient()}>
        <OcrEditor
          documentId="doc-1"
          page={1}
          initialText="updated text"
          lockVersion={3}
          parentRevisionId="rev-1"
          revision={{ id: "rev-1", status: "draft" }}
          onLockVersionChange={onLockVersionChange}
        />
      </QueryClientProvider>,
    );

    await user.type(screen.getByPlaceholderText("Edit reason"), "fixed a typo");
    await user.click(screen.getByRole("button", { name: "Save draft" }));

    await waitFor(() => expect(onLockVersionChange).toHaveBeenCalledWith(4));
    expect(saveDraftPage).toHaveBeenLastCalledWith(
      "doc-1",
      1,
      { text: "updated text", parent_revision_id: "rev-1", edit_reason: "fixed a typo" },
      { idempotencyKey: expect.any(String), lockVersion: 3 },
    );
  });

  it("notifies the workspace with the saved page and lock version", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const savedPage = {
      page_revision_id: "page-revision-2",
      lock_version: 4,
      page_number: 1,
      text: "saved",
      status: "draft",
    };
    vi.mocked(saveDraftPage).mockResolvedValue(savedPage);

    render(
      <QueryClientProvider client={queryClient}>
        <OcrEditor
          documentId="doc-1"
          page={1}
          initialText="local correction"
          lockVersion={3}
          parentRevisionId="page-revision-1"
          revision={{ id: "revision-set-1", status: "draft" }}
          onSaved={onSaved}
        />
      </QueryClientProvider>,
    );

    await user.type(screen.getByPlaceholderText("Edit reason"), "exact parent");
    await user.click(screen.getByRole("button", { name: "Save draft" }));

    await vi.waitFor(() => expect(onSaved).toHaveBeenCalledWith(savedPage));
  });
});
