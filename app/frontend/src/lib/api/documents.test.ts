import { describe, expect, it, vi } from "vitest";

vi.mock("../api-client", () => ({
  apiFetch: vi.fn(),
  apiFetchBlob: vi.fn(),
}));

import { apiFetch, apiFetchBlob } from "../api-client";
import { getDocumentBlob, createUploadSession, finalizeUpload } from "./documents";

describe("getDocumentBlob", () => {
  it("uses the protected content endpoint", async () => {
    const blob = new Blob(["pdf"], { type: "application/pdf" });
    vi.mocked(apiFetchBlob).mockResolvedValue(blob);

    await expect(getDocumentBlob("doc-123")).resolves.toBe(blob);
    expect(apiFetchBlob).toHaveBeenCalledWith("/documents/doc-123/content");
  });
});

describe("createUploadSession and finalizeUpload", () => {
  it("sends Idempotency-Key when creating an upload session", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      document_id: "doc-1",
      upload_id: "upl-1",
      object_key: "key-1",
      state: "pending_upload",
      required_headers: {},
    });
    await createUploadSession(
      {
        patient_id: "patient-1",
        filename: "test.pdf",
        expected_size: 12345,
        expected_sha256: "hash123",
        claimed_mime_type: "application/pdf",
      },
      { idempotencyKey: "sess-key-1" },
    );
    expect(apiFetch).toHaveBeenCalledWith(
      "/documents/upload-sessions",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Idempotency-Key": "sess-key-1" }),
      }),
    );
  });

  it("finalizes upload session with documentId and uploadId", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      id: "res-1",
      document_id: "doc-1",
      state: "finalized",
    });
    await finalizeUpload("doc-1", "upl-1", { idempotencyKey: "finalize-key-1" });
    expect(apiFetch).toHaveBeenCalledWith(
      "/documents/doc-1/uploads/upl-1/finalize",
      expect.objectContaining({
        method: "POST",
        headers: { "Idempotency-Key": "finalize-key-1" },
      }),
    );
  });
});
