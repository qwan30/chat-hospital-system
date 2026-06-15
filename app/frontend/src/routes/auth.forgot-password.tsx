import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthSplitLayout } from "@/components/shell/AuthSplitLayout";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { CheckCircle2, ShieldCheck } from "lucide-react";

export const Route = createFileRoute("/auth/forgot-password")({
  head: () => ({ meta: [{ title: "Forgot password — HMS AI Copilot" }] }),
  component: ForgotPassword,
});

function ForgotPassword() {
  const [sent, setSent] = useState(false);
  return (
    <AuthSplitLayout>
      <Card className="p-7">
        <h1 className="text-2xl font-semibold tracking-tight">Reset your password</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          We'll email a secure link to your hospital address. SSO users should contact IT instead.
        </p>
        {sent ? (
          <div className="mt-6 flex items-start gap-3 rounded-md border border-success/30 bg-success/5 p-4">
            <CheckCircle2 className="mt-0.5 h-5 w-5 text-success" />
            <div className="text-sm">
              <div className="font-semibold text-success">Reset link sent</div>
              <p className="text-muted-foreground">If the address matches an account, you'll receive a one-time reset link within 5 minutes.</p>
            </div>
          </div>
        ) : (
          <form
            className="mt-6 space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              setSent(true);
            }}
          >
            <div className="space-y-1.5">
              <Label htmlFor="email">Hospital email</Label>
              <Input id="email" type="email" placeholder="you@hospital.org" required />
            </div>
            <Button type="submit" className="w-full">Send reset link</Button>
          </form>
        )}
        <div className="mt-6 flex items-center justify-between text-xs text-muted-foreground">
          <Link to="/auth/login" className="hover:text-foreground">← Back to sign in</Link>
          <a href="mailto:it-helpdesk@hospital.org" className="hover:text-foreground">Contact IT helpdesk</a>
        </div>
        <div className="mt-6 flex items-center gap-2 rounded-md border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5 text-success" />
          All password resets are audit-logged.
        </div>
      </Card>
    </AuthSplitLayout>
  );
}