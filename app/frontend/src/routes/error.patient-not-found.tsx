import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/error/patient-not-found")({
  head: () => ({ meta: [{ title: "404 Patient not found" }] }),
  component: () => (
    <ErrorState
      code="404"
      title="Patient not found"
      description="The MRN you opened is missing from the synced cache or no longer in your scope. Try searching again, or trigger a manual HMS sync."
      cta={{ label: "Back to patients", to: "/patients" }}
      tone="info"
    />
  ),
});
