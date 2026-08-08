/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
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

beforeEach(() => {
  vi.mocked(saveDraftPage).mockReset();
});

afterEach(() => {
  cleanup();
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
          parentRevisionId="page-revision-1"
          revision={{ id: "rev-1", text: "old text", status: "draft" }}
        />
      </QueryClientProvider>,
    );

    await user.type(screen.getByPlaceholderText("Edit reason"), "fixed a typo");
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    expect(screen.getByDisplayValue("local correction")).toBeVisible();
    expect(screen.getByRole("button", { name: "Compare with latest" })).toBeVisible();
  });

  it("uses the returned lock version for the next draft save", async () => {
    const user = userEvent.setup();
    vi.mocked(saveDraftPage)
      .mockResolvedValueOnce({
        page_revision_id: "page-rev-1",
        lock_version: 4,
        page_number: 1,
        text: "first save",
        status: "draft",
      })
      .mockResolvedValueOnce({
        page_revision_id: "page-rev-1",
        lock_version: 5,
        page_number: 1,
        text: "second save",
        status: "draft",
      });

    render(
      <QueryClientProvider client={queryClient}>
        <OcrEditor
          documentId="doc-1"
          page={1}
          initialText="local correction"
          lockVersion={3}
          parentRevisionId="page-revision-1"
          revision={{ id: "rev-1", status: "draft" }}
        />
      </QueryClientProvider>,
    );

    await user.type(screen.getByPlaceholderText("Edit reason"), "first change");
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    await vi.waitFor(() => expect(saveDraftPage).toHaveBeenCalledTimes(1));

    await user.type(screen.getByPlaceholderText("Edit reason"), "second change");
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    await vi.waitFor(() => expect(saveDraftPage).toHaveBeenCalledTimes(2));

    expect(vi.mocked(saveDraftPage).mock.calls[1][3]).toEqual(
      expect.objectContaining({ lockVersion: 4 }),
    );
  });

  it("writes against the exact page revision rather than a revision-set id", async () => {
    const user = userEvent.setup();
    vi.mocked(saveDraftPage).mockResolvedValue({
      page_revision_id: "page-revision-1",
      lock_version: 4,
      page_number: 1,
      text: "saved",
      status: "draft",
    });

    render(
      <QueryClientProvider client={queryClient}>
        <OcrEditor
          documentId="doc-1"
          page={1}
          initialText="local correction"
          lockVersion={3}
          parentRevisionId="page-revision-1"
          revision={{ id: "revision-set-1", status: "draft" }}
        />
      </QueryClientProvider>,
    );

    await user.type(screen.getByPlaceholderText("Edit reason"), "exact parent");
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    await vi.waitFor(() => expect(saveDraftPage).toHaveBeenCalledTimes(1));

    expect(vi.mocked(saveDraftPage).mock.calls[0][2]).toEqual(
      expect.objectContaining({
        text: "local correction",
        parent_revision_id: "page-revision-1",
      }),
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
