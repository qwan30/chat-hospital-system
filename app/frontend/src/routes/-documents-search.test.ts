import { describe, expect, it, vi } from "vitest";
import { canSearchDocuments, submitDocumentSearch } from "./_app.documents.search";

describe("canSearchDocuments", () => {
  it("does not search a q-only legacy link without a patient scope", () => {
    expect(canSearchDocuments("apixaban", "")).toBe(false);
  });

  it("requires a non-empty query as well as an explicit patient scope", () => {
    expect(canSearchDocuments("", "patient-123")).toBe(false);
  });

  it("allows a query when the patient scope is explicit", () => {
    expect(canSearchDocuments("apixaban", "patient-123")).toBe(true);
  });

  it("submits the current URL patient scope in the exact API payload", () => {
    const mutate = vi.fn();

    submitDocumentSearch(mutate, "apixaban", "patient-from-url");

    expect(mutate).toHaveBeenCalledWith({
      patient_id: "patient-from-url",
      query: "apixaban",
      top_k: 5,
    });
  });

  it("does not submit an API payload when the URL has no patient scope", () => {
    const mutate = vi.fn();

    submitDocumentSearch(mutate, "apixaban", "");

    expect(mutate).not.toHaveBeenCalled();
  });
});
