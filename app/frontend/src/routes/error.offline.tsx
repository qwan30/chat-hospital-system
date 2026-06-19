import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";
import { Button } from "@/components/ui/button";
import { getError } from "@/lib/errors";

export const Route = createFileRoute("/error/offline")({
  head: () => ({ meta: [{ title: "Offline" }] }),
  component: () => {
    const e = getError("offline");
    return (
      <ErrorState
        code="OFFLINE"
        title={e.title}
        description={e.description}
        tone={e.tone}
        extra={
          <Button variant="outline" onClick={() => window.location.reload()}>
            Retry
          </Button>
        }
      />
    );
  },
});
