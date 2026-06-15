import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Wordmark } from "@/components/hms/Logo";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Lock, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/auth/mfa")({
  head: () => ({
    meta: [
      { title: "Verify identity — HMS AI Copilot" },
      { name: "description", content: "Multi-factor verification for HMS AI Copilot." },
    ],
  }),
  component: MfaPage,
});

function MfaPage() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [secs, setSecs] = useState(105);
  useEffect(() => {
    if (secs <= 0) return;
    const t = setTimeout(() => setSecs((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [secs]);
  const mm = String(Math.floor(secs / 60)).padStart(2, "0");
  const ss = String(secs % 60).padStart(2, "0");

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <Wordmark />
      <div className="mt-8 w-full max-w-md rounded-2xl border bg-card p-8 shadow-sm">
        <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Lock className="h-5 w-5" />
        </div>
        <h2 className="text-xl font-semibold tracking-tight">Verify your identity</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          We sent a 6-digit code to <span className="font-medium text-foreground">s***@hospital.org</span>.
        </p>
        <div className="my-6 flex justify-center">
          <InputOTP maxLength={6} value={code} onChange={setCode}>
            <InputOTPGroup>
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <InputOTPSlot key={i} index={i} />
              ))}
            </InputOTPGroup>
          </InputOTP>
        </div>
        <div className="mb-4 flex items-center justify-between text-xs">
          <span className={secs > 0 ? "text-muted-foreground" : "text-destructive"}>
            {secs > 0 ? `Code expires in ${mm}:${ss}` : "Code expired"}
          </span>
          <button className="font-medium text-primary hover:underline" onClick={() => setSecs(120)}>
            Resend
          </button>
        </div>
        <div className="mb-4 space-y-2">
          <label className="text-xs uppercase tracking-wider text-muted-foreground">
            Use another method
          </label>
          <Select defaultValue="email">
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="email">Email · s***@hospital.org</SelectItem>
              <SelectItem value="sms">SMS · (***) ***-2841</SelectItem>
              <SelectItem value="totp">Authenticator app</SelectItem>
              <SelectItem value="key">Security key (YubiKey)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button
          className="w-full"
          disabled={code.length < 6}
          onClick={() => navigate({ to: "/dashboard" })}
        >
          Verify & continue →
        </Button>
      </div>
      <p className="mt-6 inline-flex items-center gap-2 text-xs text-muted-foreground">
        <ShieldCheck className="h-3 w-3 text-success" /> Your data is protected · MFA required ·
        Audit-ready
      </p>
    </div>
  );
}