const retrievableDocumentStatuses = new Set(["ready", "ready_with_warnings", "indexed"]);

/**
 * The API's current retrieval-ready states plus the legacy status retained for
 * existing records. Keep UI gating and counts on this one contract.
 */
export function isDocumentReadyForRetrieval(status: string | null | undefined): boolean {
  return status !== undefined && status !== null && retrievableDocumentStatuses.has(status);
}
