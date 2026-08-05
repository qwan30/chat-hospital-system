/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
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
          revision={{ id: "rev-1", text: "old text", status: "draft" }}
        />
      </QueryClientProvider>,
    );

    await user.type(screen.getByPlaceholderText("Edit reason"), "fixed a typo");
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    expect(screen.getByDisplayValue("local correction")).toBeVisible();
    expect(screen.getByRole("button", { name: "Compare with latest" })).toBeVisible();
  });
});
