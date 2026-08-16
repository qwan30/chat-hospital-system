import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getAccessRequest, reviewAccessRequest } from "@/lib/api/access-requests";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/hms/ErrorState";
import { toast } from "sonner";

import { sanitizeError } from "@/lib/errors";
import { useSession } from "@/lib/session";
import { Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/access-requests/$requestId/review")({
  head: () => ({ meta: [{ title: "Review request — HMS AI Copilot" }] }),
  component: Page,
  errorComponent: ({ error, reset }) => (
    <AppShell fixedHeight>
      <div className="flex h-full items-center justify-center p-8">
        <ErrorState
          title="Failed to load access request"
          description={sanitizeError(error)}
          code="API_ERROR"
          extra={
            <Button onClick={reset} variant="outline">
              Retry
            </Button>
          }
        />
      </div>
    </AppShell>
  ),
});

function Page() {
  const { requestId } = Route.useParams();
  const navigate = useNavigate();
  const [notes, setNotes] = useState("");

  const {
    data: r,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["access-request", requestId],
    queryFn: () => getAccessRequest(requestId),
    retry: false,
  });

  const { session } = useSession();

  const mutation = useMutation({
    mutationFn: (status: "approved" | "denied" | "pending_info") =>
      reviewAccessRequest(requestId, { status, notes }),
    onSuccess: (data) => {
      toast.success(`Request ${data.status}`);
      navigate({ to: "/access-requests" });
    },
    onError: (err: Error) => {
      toast.error("Failed to submit review", { description: err.message });
    },
  });

  if (session && session.role !== "admin" && session.role !== "security") {
    return <Navigate to="/dashboard" replace />;
  }

  if (isLoading) {
    return (
      <AppShell>
        <PageHeader title="Loading..." />
      </AppShell>
    );
  }

  if (error || !r) {
    return (
      <AppShell>
        <PageHeader title="Request not found" />
        <ErrorState
          code="API_ERROR"
          title="Failed to load access request"
          description={sanitizeError(error)}
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title="Review access request"
        description={`${r.patient_name} · ${r.patient_mrn}`}
        backLink={{ to: "/access-requests", label: "Back to Access Requests" }}
      />
      <Card className="p-6 space-y-4">
        <div className="rounded-md border bg-muted/40 p-4 text-sm">
          <p className="font-medium">
            {r.requester_name} · {r.requester_role}
          </p>
          <p className="mt-1 text-muted-foreground">{r.justification}</p>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Reviewer note (audited)</label>
          <Textarea
            placeholder="Document scope, duration, and conditions for this access grant…"
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={mutation.isPending}
          />
        </div>
        <div className="flex gap-2 justify-end">
          <Button
            variant="outline"
            onClick={() => mutation.mutate("pending_info")}
            disabled={mutation.isPending || !notes.trim()}
            title={!notes.trim() ? "Notes are required to request more info" : ""}
          >
            Request info
          </Button>
          <Button
            variant="outline"
            className="text-destructive hover:bg-destructive/10"
            onClick={() => mutation.mutate("denied")}
            disabled={mutation.isPending || !notes.trim()}
            title={!notes.trim() ? "A reason is required to deny" : ""}
          >
            Deny
          </Button>
          <Button
            variant="default"
            onClick={() => mutation.mutate("approved")}
            disabled={mutation.isPending}
          >
            Approve
          </Button>
        </div>
      </Card>
    </AppShell>
  );
}
