import { describe, expect, it } from "vitest";

import { hasStreamScopeChanged, isCurrentStreamRequest } from "./stream-scope";

describe("hasStreamScopeChanged", () => {
  it("keeps a new-thread stream alive after the request adopts the created thread", () => {
    expect(
      hasStreamScopeChanged(
        { patientId: undefined, threadId: "thread-new" },
        { patientId: undefined, threadId: "thread-new" },
      ),
    ).toBe(false);
  });

  it("detects genuine patient and thread context changes", () => {
    expect(
      hasStreamScopeChanged(
        { patientId: "patient-a", threadId: "thread-a" },
        { patientId: "patient-b", threadId: "thread-a" },
      ),
    ).toBe(true);
    expect(
      hasStreamScopeChanged(
        { patientId: "patient-a", threadId: "thread-a" },
        { patientId: "patient-a", threadId: "thread-b" },
      ),
    ).toBe(true);
  });

  it("rejects state writes from an aborted request after a newer request starts", () => {
    const oldRequest = new AbortController();
    const newRequest = new AbortController();

    expect(isCurrentStreamRequest(newRequest, oldRequest)).toBe(false);
    expect(isCurrentStreamRequest(newRequest, newRequest)).toBe(true);
  });

  it("invalidates a request while its attachment upload is still pending", () => {
    const uploadRequest = new AbortController();
    let activeRequest: AbortController | null = uploadRequest;

    activeRequest = null;

    expect(isCurrentStreamRequest(activeRequest, uploadRequest)).toBe(false);
  });
});
