import { createFileRoute } from "@tanstack/react-router";
import { AuthSplitLayout } from "@/components/shell/AuthSplitLayout";
import { Card } from "@/components/ui/card";
import { Loader2, CheckCircle2 } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/auth/sso/callback")({
  head: () => ({ meta: [{ title: "Signing in — HMS AI Copilot" }] }),
  component: SsoCallback,
});

export function SsoCallback() {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();
  const processed = useRef(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const steps = [
    "Verifying SSO assertion…",
    "Exchanging tokens with hospital IDP…",
    "Loading clinician profile and roles…",
    "Redirecting to dashboard…",
  ];

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");
    const errorParam = url.searchParams.get("error");

    // Xóa sạch `code`/`state` khỏi `window.history` bằng `replaceState`
    url.searchParams.delete("code");
    url.searchParams.delete("state");
    url.searchParams.delete("session_state");
    url.searchParams.delete("error");
    window.history.replaceState({}, "", url.toString());

    // Fail-closed an toàn
    if (errorParam || !code || !state) {
      setErrorMsg("Invalid SSO response from provider.");
      return;
    }

    const t = setInterval(() => {
      setStep((s) => {
        const next = s + 1;
        if (next >= steps.length) {
          clearInterval(t);
          navigate({ to: "/dashboard" });
          return s;
        }
        return next;
      });
    }, 700);

    return () => clearInterval(t);
  }, [navigate, steps.length]);

  if (errorMsg) {
    return (
      <AuthSplitLayout>
        <Card className="p-8">
          <ErrorState title="SSO Sign In Failed" description={errorMsg} code="API_ERROR" />
        </Card>
      </AuthSplitLayout>
    );
  }
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
