import { describe, expect, it } from "vitest";
import { isDocumentReadyForRetrieval } from "./document-status";

describe("isDocumentReadyForRetrieval", () => {
  it.each(["ready", "ready_with_warnings", "indexed"])("accepts %s as retrievable", (status) => {
    expect(isDocumentReadyForRetrieval(status)).toBe(true);
  });

  it.each(["uploaded", "indexing", "index_failed"])(
    "does not accept %s as retrievable",
    (status) => {
      expect(isDocumentReadyForRetrieval(status)).toBe(false);
    },
  );
});
