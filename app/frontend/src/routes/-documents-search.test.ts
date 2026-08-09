import { describe, expect, it } from "vitest";
import { canSearchDocuments } from "./_app.documents.search";

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
});
