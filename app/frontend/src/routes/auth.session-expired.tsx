import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthSplitLayout } from "@/components/shell/AuthSplitLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Clock } from "lucide-react";

export const Route = createFileRoute("/auth/session-expired")({
  head: () => ({ meta: [{ title: "Session expired — HMS AI Copilot" }] }),
  component: SessionExpired,
});

function SessionExpired() {
  return (
    <AuthSplitLayout>
      <Card className="p-7">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-warning/10 text-warning">
          <Clock className="h-6 w-6" />
        </div>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight">Session expired</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          For security, your session timed out after 30 minutes of inactivity. Please sign in again to continue.
          Any unsaved chat drafts are preserved on this device.
        </p>
        <div className="mt-6 flex gap-2">
          <Button asChild className="flex-1"><Link to="/auth/login">Sign in again</Link></Button>
          <Button asChild variant="outline"><Link to="/auth/forgot-password">Forgot password</Link></Button>
        </div>
        <p className="mt-6 rounded-md border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
          Session ID <span className="font-mono text-foreground">sess-9f3a-71c2</span> · expired 16:08 UTC · logged in audit trail.
        </p>
      </Card>
    </AuthSplitLayout>
  );
}