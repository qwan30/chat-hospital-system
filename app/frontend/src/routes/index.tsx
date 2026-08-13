import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { useSession } from "@/lib/session";

export const Route = createFileRoute("/")({
  component: IndexPage,
});

function IndexPage() {
  const { session, hydrated } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    if (!hydrated) return;
    if (session) {
      navigate({ to: "/chat", replace: true });
    } else {
      navigate({ to: "/auth/login", replace: true });
    }
  }, [hydrated, session, navigate]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Loading workspace…
      </div>
    );
  }

  return null;
}
