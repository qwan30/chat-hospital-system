import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";
import { getError } from "@/lib/errors";

export const Route = createFileRoute("/error/maintenance")({
  head: () => ({ meta: [{ title: "Scheduled maintenance" }] }),
  component: () => {
    const e = getError("maintenance");
    return <ErrorState code="503" title={e.title} description={e.description} tone={e.tone} />;
  },
});
