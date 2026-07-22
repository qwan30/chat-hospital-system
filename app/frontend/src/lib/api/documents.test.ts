import { describe, expect, it, vi } from "vitest";

vi.mock("../api-client", () => ({
  apiFetch: vi.fn(),
  apiFetchBlob: vi.fn(),
}));

import { apiFetchBlob } from "../api-client";
import { getDocumentBlob } from "./documents";

describe("getDocumentBlob", () => {
  it("uses the protected content endpoint", async () => {
    const blob = new Blob(["pdf"], { type: "application/pdf" });
    vi.mocked(apiFetchBlob).mockResolvedValue(blob);

    await expect(getDocumentBlob("doc-123")).resolves.toBe(blob);
    expect(apiFetchBlob).toHaveBeenCalledWith("/documents/doc-123/content");
  });
});
