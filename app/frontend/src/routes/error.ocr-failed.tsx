import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/error/ocr-failed")({
  head: () => ({ meta: [{ title: "422 OCR failed" }] }),
  component: () => (
    <ErrorState
      code="422"
      title="OCR processing failed"
      description="The uploaded scan is too low contrast or rotated to extract structured fields. You can re-upload a higher-quality scan or open it in the review tool."
      cta={{ label: "Open OCR queue", to: "/documents/ocr-queue" }}
      tone="warning"
    />
  ),
});