import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/error/insufficient-evidence")({
  head: () => ({ meta: [{ title: "422 Insufficient evidence" }] }),
  component: () => (
    <ErrorState
      code="422"
      title="Insufficient evidence to answer"
      description="The retrieval pipeline could not surface citations of high enough relevance to answer safely. Try rephrasing, narrowing patient scope, or uploading the missing source document."
      cta={{ label: "Upload document", to: "/documents/upload" }}
      tone="warning"
    />
  ),
});
