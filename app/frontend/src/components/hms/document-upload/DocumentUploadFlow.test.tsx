/** @vitest-environment jsdom */
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { DocumentUploadFlow } from "./DocumentUploadFlow";
import { createUploadSession, finalizeUpload, putPresignedObject } from "@/lib/api/documents";

vi.mock("@/lib/api/documents", () => ({
  createUploadSession: vi.fn(),
  finalizeUpload: vi.fn(),
  putPresignedObject: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => mockNavigate,
}));

describe("DocumentUploadFlow", () => {
  const syntheticPdf = new File(["dummy content"], "test.pdf", { type: "application/pdf" });

  afterEach(() => {
    cleanup();
    document.body.innerHTML = "";
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const completeUpload = async (user: ReturnType<typeof userEvent.setup>, file: File) => {
    await user.upload(screen.getByLabelText(/Clinical document/i), file);
    await user.click(screen.getByRole("button", { name: /Upload document/i }));
  };

  it("uploads directly with every server-required header before finalization", async () => {
    const user = userEvent.setup();
    const sessionMock = {
      document_id: "doc-1",
      upload_id: "up-1",
      upload_url: "https://r2.example.com/upload",
      required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
      state: "pending_upload",
      object_key: "key-1",
      presigned_url: "https://r2.example.com/upload",
    };
    vi.mocked(createUploadSession).mockResolvedValue(sessionMock);
    vi.mocked(putPresignedObject).mockResolvedValue();
    vi.mocked(finalizeUpload).mockResolvedValue({
      id: "res-1",
      document_id: "doc-1",
      state: "finalized",
    });

    render(<DocumentUploadFlow patientId="patient-1" />);
    await user.upload(screen.getByLabelText(/Clinical document/i), syntheticPdf);
    await user.click(screen.getByRole("button", { name: /Upload document/i }));

    await waitFor(() => {
      expect(createUploadSession).toHaveBeenCalledTimes(1);
    });

    expect(putPresignedObject).toHaveBeenCalledWith(
      expect.objectContaining({
        required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
      }),
      syntheticPdf,
      expect.any(Function),
    );

    // Ensure PUT happened before finalize
    const putOrder = vi.mocked(putPresignedObject).mock.invocationCallOrder[0];
    const finalizeOrder = vi.mocked(finalizeUpload).mock.invocationCallOrder[0];
    expect(putOrder).toBeLessThan(finalizeOrder);
  });

  it.each(["quarantined", "rejected"])("never presents %s as ready for OCR", async (state) => {
    const user = userEvent.setup();
    const sessionMock = {
      document_id: "doc-1",
      upload_id: "up-1",
      upload_url: "https://r2.example.com/upload",
      required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
      state: "pending_upload",
      object_key: "key-1",
      presigned_url: "https://r2.example.com/upload",
    };
    vi.mocked(createUploadSession).mockResolvedValue(sessionMock);
    vi.mocked(putPresignedObject).mockResolvedValue();
    vi.mocked(finalizeUpload).mockResolvedValue({ id: "res-1", document_id: "doc-1", state });

    render(<DocumentUploadFlow patientId="patient-1" />);
    await completeUpload(user, syntheticPdf);

    await waitFor(() => {
      expect(screen.queryByText("OCR started")).toBeNull();
      expect(
        screen.getByText(state === "quarantined" ? "Upload quarantined" : "Upload rejected"),
      ).not.toBeNull();
    });
  });

  it("fails closed when finalization returns an unknown lifecycle state", async () => {
    const user = userEvent.setup();
    const sessionMock = {
      document_id: "doc-1",
      upload_id: "up-1",
      required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
      state: "pending_upload",
      object_key: "key-1",
      presigned_url: "https://r2.example.com/upload",
    };
    vi.mocked(createUploadSession).mockResolvedValue(sessionMock);
    vi.mocked(putPresignedObject).mockResolvedValue();
    vi.mocked(finalizeUpload).mockResolvedValue({
      id: "res-1",
      document_id: "doc-1",
      state: "unexpected_state",
    });

    render(<DocumentUploadFlow patientId="patient-1" />);
    await completeUpload(user, syntheticPdf);

    await waitFor(() => {
      expect(screen.getByText("Upload rejected")).not.toBeNull();
      expect(screen.getByText(/Unsupported upload lifecycle state/)).not.toBeNull();
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("handles a 412 conflict error from putPresignedObject as a rejected state", async () => {
    const user = userEvent.setup();
    const sessionMock = {
      document_id: "doc-1",
      upload_id: "up-1",
      required_headers: { "Content-Type": "application/pdf", "If-None-Match": "*" },
      state: "pending_upload",
      object_key: "key-1",
      presigned_url: "https://r2.example.com/upload",
    };
    vi.mocked(createUploadSession).mockResolvedValue(sessionMock);

    // Mock putPresignedObject to throw a 412 conflict error
    vi.mocked(putPresignedObject).mockRejectedValue(
      new Error("Immutable object key already exists"),
    );

    render(<DocumentUploadFlow patientId="patient-1" />);
    await completeUpload(user, syntheticPdf);

    await waitFor(() => {
      expect(screen.getByText("Upload rejected")).not.toBeNull();
      expect(screen.getByText(/Immutable object key already exists/)).not.toBeNull();
    });
  });
});
