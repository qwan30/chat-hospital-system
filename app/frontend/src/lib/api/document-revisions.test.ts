import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api-client", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../api-client";
import {
  saveDraftPage,
  submitDraft,
  approveRevisionSet,
  rejectRevisionSet,
  restoreRevision,
  listRevisionSets,
} from "./document-revisions";

describe("document-revisions client", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
  });

  it("sends Idempotency-Key and If-Match on draft save", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ page_revision_id: "rev-1" });
    const payload = {
      text: "Updated clinical text",
      parent_revision_id: "prev-1",
      edit_reason: "Typo fix",
    };
    await saveDraftPage("doc-1", 2, payload, { idempotencyKey: "draft-1", lockVersion: 7 });

    expect(apiFetch).toHaveBeenCalledWith(
      expect.stringContaining("/documents/doc-1/draft/pages/2"),
      expect.objectContaining({
        method: "PATCH",
        headers: expect.objectContaining({ "Idempotency-Key": "draft-1", "If-Match": "7" }),
        body: JSON.stringify(payload),
      }),
    );
  });

  it("sends Idempotency-Key and If-Match on submitDraft", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ revision_set_id: "set-1" });
    await submitDraft("doc-1", { idempotencyKey: "submit-1", lockVersion: 10 });

    expect(apiFetch).toHaveBeenCalledWith(
      "/documents/doc-1/draft/submit",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Idempotency-Key": "submit-1", "If-Match": "10" }),
      }),
    );
  });

  it("sends Idempotency-Key without If-Match on approveRevisionSet when lockVersion is omitted", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ generation_id: "gen-1", state: "started" });
    await approveRevisionSet(
      "doc-1",
      "set-1",
      { demo_mode: false },
      { idempotencyKey: "approve-1" },
    );

    expect(apiFetch).toHaveBeenCalledWith(
      "/documents/doc-1/revision-sets/set-1/approve",
      expect.objectContaining({
        method: "POST",
        headers: { "Idempotency-Key": "approve-1" },
      }),
    );
  });

  it("calls rejectRevisionSet, restoreRevision, and listRevisionSets", async () => {
    vi.mocked(apiFetch).mockResolvedValue({});
    await rejectRevisionSet(
      "doc-1",
      "set-1",
      { reason: "Bad text" },
      { idempotencyKey: "reject-1" },
    );
    expect(apiFetch).toHaveBeenCalledWith(
      "/documents/doc-1/revision-sets/set-1/reject",
      expect.objectContaining({ method: "POST" }),
    );

    await restoreRevision(
      "doc-1",
      "set-1",
      { revision_id: "rev-0" },
      { idempotencyKey: "restore-1" },
    );
    expect(apiFetch).toHaveBeenCalledWith(
      "/documents/doc-1/revision-sets/set-1/restore",
      expect.objectContaining({ method: "POST" }),
    );

    await listRevisionSets("doc-1");
    expect(apiFetch).toHaveBeenCalledWith("/documents/doc-1/revision-sets");
  });
});
