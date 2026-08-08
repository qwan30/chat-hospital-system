import { describe, expect, it, vi } from "vitest";

vi.mock("../api-client", () => ({
  apiFetch: vi.fn(),
  apiFetchBlob: vi.fn(),
  getStoredApiUrl: vi.fn(() => "/api"),
  getToken: vi.fn(() => "dev-token"),
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
    await finalizeUpload("doc-1", "upl-1");
    expect(apiFetch).toHaveBeenCalledWith(
      "/documents/doc-1/uploads/upl-1/finalize",
      expect.objectContaining({ method: "POST" }),
    );
  });
});

describe("putPresignedObject", () => {
  it("sends every immutable signed header, including If-None-Match", async () => {
    class MockXMLHttpRequest {
      static latest: MockXMLHttpRequest;
      upload = {};
      open = vi.fn();
      setRequestHeader = vi.fn();
      status = 200;
      onload: (() => void) | undefined;
      onerror: (() => void) | undefined;
      send = vi.fn(() => this.onload?.());
      constructor() {
        MockXMLHttpRequest.latest = this;
      }
    }
    vi.stubGlobal("XMLHttpRequest", MockXMLHttpRequest);

    await putPresignedObject(
      {
        document_id: "doc-1",
        upload_id: "upl-1",
        object_key: "key-1",
        presigned_url: "https://r2.example.com/upload",
        required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
        state: "pending_upload",
      },
      new File(["pdf"], "test.pdf", { type: "application/pdf" }),
      vi.fn(),
    );

    expect(MockXMLHttpRequest.latest.setRequestHeader).toHaveBeenCalledWith(
      "Content-Type",
      "application/pdf",
    );
    expect(MockXMLHttpRequest.latest.setRequestHeader).toHaveBeenCalledWith("If-None-Match", "*");
  });

  it("maps the local storage marker to the authenticated API upload endpoint", async () => {
    class MockXMLHttpRequest {
      static latest: MockXMLHttpRequest;
      upload = {};
      open = vi.fn();
      setRequestHeader = vi.fn();
      status = 204;
      onload: (() => void) | undefined;
      onerror: (() => void) | undefined;
      send = vi.fn(() => this.onload?.());
      constructor() {
        MockXMLHttpRequest.latest = this;
      }
    }
    vi.stubGlobal("XMLHttpRequest", MockXMLHttpRequest);

    await putPresignedObject(
      {
        document_id: "doc-1",
        upload_id: "upl-1",
        object_key: "source/patient-1/doc-1/upl-1/original.pdf",
        presigned_url: "local://source/patient-1/doc-1/upl-1/original.pdf",
        required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
        state: "pending_upload",
      },
      new File(["pdf"], "test.pdf", { type: "application/pdf" }),
      vi.fn(),
    );

    expect(MockXMLHttpRequest.latest.open).toHaveBeenCalledWith(
      "PUT",
      "/api/documents/upload-objects/source/patient-1/doc-1/upl-1/original.pdf",
      true,
    );
  });

  it("rejects a presigned upload contract that does not protect the immutable key", async () => {
    const open = vi.fn();
    class MockXMLHttpRequest {
      upload = {};
      open = open;
      setRequestHeader = vi.fn();
      send = vi.fn();
    }
    vi.stubGlobal("XMLHttpRequest", MockXMLHttpRequest);

    await expect(
      putPresignedObject(
        {
          document_id: "doc-1",
          upload_id: "upl-1",
          object_key: "key-1",
          presigned_url: "https://r2.example.com/upload",
          required_headers: { "Content-Type": "application/pdf" },
          state: "pending_upload",
        },
        new File(["pdf"], "test.pdf", { type: "application/pdf" }),
        vi.fn(),
      ),
    ).rejects.toThrow("If-None-Match: *");
    expect(open).not.toHaveBeenCalled();
  });
});
