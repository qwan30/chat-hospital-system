import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";
import { getError } from "@/lib/errors";

export const Route = createFileRoute("/error/server")({
  head: () => ({ meta: [{ title: "500 Server error" }] }),
  component: () => {
    const e = getError("unknown");
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
