/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentWorkspace } from "./DocumentWorkspace";
import { restoreRevision } from "@/lib/api/document-revisions";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom/vitest";

vi.mock("@/lib/api/document-revisions", () => ({
  restoreRevision: vi.fn(),
  listRevisionSets: vi.fn().mockResolvedValue([]),
}));

vi.mock("@/lib/api/documents", () => ({
  getDocument: vi.fn().mockResolvedValue({ id: "doc-1", mime_type: "application/pdf" }),
}));

const queryClient = new QueryClient();

describe("DocumentWorkspace", () => {
  it("keeps a historical revision read-only and restores as a new child", async () => {
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={queryClient}>
        <DocumentWorkspace documentId="doc-1" />
      </QueryClientProvider>
    );

    // This will fail because Revision is not there yet, etc.
    await user.selectOptions(screen.getByLabelText("Revision"), "rev-1");
    expect(screen.getByRole("textbox", { name: "Corrected page text" })).toHaveAttribute("readonly");
    await user.click(screen.getByRole("button", { name: "Restore as new revision" }));
    expect(restoreRevision).toHaveBeenCalledWith("doc-1", "rev-1", expect.any(Object), expect.any(Object));
  });
});
