import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";
import { Button } from "@/components/ui/button";
import { getError } from "@/lib/errors";

export const Route = createFileRoute("/error/conflict")({
  head: () => ({ meta: [{ title: "409 Conflict" }] }),
  component: () => {
    const e = getError("conflict");
    return (
      <ErrorState
        code={String(e.http)}
        title={e.title}
        description={e.description}
        tone={e.tone}
        extra={
          <Button variant="outline" onClick={() => window.location.reload()}>
            Reload latest
          </Button>
        }
      />
    );
  },
});
