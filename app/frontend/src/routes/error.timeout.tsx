import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";
import { getError } from "@/lib/errors";

export const Route = createFileRoute("/error/timeout")({
  head: () => ({ meta: [{ title: "504 Timeout" }] }),
  component: () => {
    const e = getError("timeout");
    return (
      <ErrorState
        code={String(e.http)}
        title={e.title}
        description={e.description}
        tone={e.tone}
        cta={e.cta}
      />
    );
  },
});
