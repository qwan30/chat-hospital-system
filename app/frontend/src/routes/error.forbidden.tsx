import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";
import { useSession } from "@/lib/session";
import { landingFor, ROLE_LABEL } from "@/lib/rbac";
import { Button } from "@/components/ui/button";
import { BreakGlassDialog } from "@/components/hms/BreakGlassDialog";

type Reason = "role" | "workspace-scope" | "break-glass";

export const Route = createFileRoute("/error/forbidden")({
  head: () => ({ meta: [{ title: "403 Forbidden" }] }),
  validateSearch: (s: Record<string, unknown>) => ({
    from: typeof s.from === "string" ? s.from : "",
    reason: (typeof s.reason === "string" ? s.reason : "role") as Reason,
  }),
  component: ForbiddenPage,
});

function ForbiddenPage() {
  const { from, reason } = Route.useSearch();
  const { session } = useSession();
  const navigate = useNavigate();
  const role = session?.role;

  const title =
    reason === "workspace-scope"
      ? "Out of workspace scope"
      : reason === "break-glass"
        ? "Break-glass access required"
        : "You don't have permission for this resource";

  const description = !role
    ? "You must be signed in to view this page."
    : reason === "workspace-scope"
      ? `${from || "This resource"} belongs to a different workspace than ${session?.workspace.name}. Switch workspace from the avatar menu to continue.`
      : reason === "break-glass"
        ? `Acting as ${ROLE_LABEL[role]}, you need emergency clinical justification to view ${from || "this record"}. All access will be audited.`
        : `Acting as ${ROLE_LABEL[role]}, you can't access ${from || "this page"}. Switch role from the avatar menu, or request access.`;

  return (
    <ErrorState
      code="403"
      title={title}
      description={description}
      tone={reason === "break-glass" ? "critical" : "warning"}
      cta={{ label: "Go to my dashboard", to: role ? landingFor(role) : "/auth/login" }}
      extra={
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => navigate({ to: "/access-requests" })}>
            Request access
          </Button>
          {reason === "break-glass" ? (
            <BreakGlassDialog
              target={from || "restricted record"}
              trigger={<Button variant="destructive">Break-glass access</Button>}
              onConfirm={() => navigate({ to: from || "/dashboard" })}
            />
          ) : null}
        </div>
      }
    />
  );
}
