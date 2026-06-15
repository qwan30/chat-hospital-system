import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";
import { getError } from "@/lib/errors";

export const Route = createFileRoute("/error/not-found")({
  head: () => ({ meta: [{ title: "404 Not found" }] }),
  component: () => {
    const e = getError("route-not-found");
    return <ErrorState code={String(e.http)} title={e.title} description={e.description} tone={e.tone} cta={e.cta} />;
  },
});