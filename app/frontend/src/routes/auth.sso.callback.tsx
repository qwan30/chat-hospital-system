import { createFileRoute } from "@tanstack/react-router";
import { AuthSplitLayout } from "@/components/shell/AuthSplitLayout";
import { Card } from "@/components/ui/card";
import { Loader2, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/auth/sso/callback")({
  head: () => ({ meta: [{ title: "Signing in — HMS AI Copilot" }] }),
  component: SsoCallback,
});

function SsoCallback() {
  const [step, setStep] = useState(0);
  const steps = [
    "Verifying SSO assertion…",
    "Exchanging tokens with hospital IDP…",
    "Loading clinician profile and roles…",
    "Redirecting to dashboard…",
  ];
  useEffect(() => {
    const t = setInterval(() => setStep((s) => Math.min(s + 1, steps.length - 1)), 700);
    return () => clearInterval(t);
  }, [steps.length]);
  return (
    <AuthSplitLayout>
      <Card className="p-8">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          {step < steps.length - 1 ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <CheckCircle2 className="h-6 w-6 text-success" />
          )}
        </div>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight">Signing you in</h1>
        <p className="mt-2 text-sm text-muted-foreground">{steps[step]}</p>
        <ul className="mt-6 space-y-2 text-sm">
          {steps.map((s, i) => (
            <li key={s} className="flex items-center gap-2">
              {i <= step ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : (
                <span className="h-4 w-4 rounded-full border" />
              )}
              <span className={i <= step ? "text-foreground" : "text-muted-foreground"}>{s}</span>
            </li>
          ))}
        </ul>
        <p className="mt-6 rounded-md border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
          Provider <span className="font-mono text-foreground">hospital-okta</span> · trace{" "}
          <span className="font-mono text-foreground">sso-tr-9214</span>
        </p>
      </Card>
    </AuthSplitLayout>
  );
}
