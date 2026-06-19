import { createFileRoute, Outlet, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect } from "react";
import { useSession } from "@/lib/session";
import { canAccess, forbiddenReason } from "@/lib/rbac";
import { useIdleTimeout } from "@/hooks/use-idle-timeout";
import { logInfo } from "@/lib/log";
import { toast } from "sonner";

export const Route = createFileRoute("/_app")({
  component: AppGate,
});

function AppGate() {
  const { session, hydrated } = useSession();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    if (!hydrated) return;
    if (!session) {
      navigate({ to: "/auth/login" });
      return;
    }
    if (!canAccess(session.role, pathname)) {
      const reason = forbiddenReason(session.role, pathname);
      logInfo("rbac.forbidden", { role: session.role, pathname, reason });
      navigate({
        to: "/error/forbidden",
        search: { from: pathname, reason } as never,
      });
    }
  }, [hydrated, session, pathname, navigate]);

  // Idle session timeout — 15 minutes of inactivity.
  useIdleTimeout(
    15 * 60 * 1000,
    () => {
      if (!session) return;
      logInfo("auth.session_expired_idle", { pathname });
      toast.warning("Session expired", {
        description: "You were signed out after 15 minutes of inactivity.",
      });
      navigate({ to: "/auth/session-expired" });
    },
    !!session,
  );

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Loading workspace…
      </div>
    );
  }
  if (!session) return null;
  return <Outlet />;
}
