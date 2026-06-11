"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Shield, Lock, ArrowLeft, Loader2, Check, FileText } from "lucide-react";


const OTP_LENGTH = 6;
const RESEND_COOLDOWN = 30;

export default function MfaPage() {
  const { login, isAuthenticated } = useAuth();
  const router = useRouter();
  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(""));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [countdown, setCountdown] = useState(RESEND_COOLDOWN);
  const [canResend, setCanResend] = useState(false);

  useEffect(() => {
    if (isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (countdown <= 0) { setCanResend(true); return; }
    const timer = setInterval(() => setCountdown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  if (isAuthenticated) return null;

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;
    const next = [...otp];
    next[index] = value;
    setOtp(next);

    // Auto-focus next input
    if (value && index < OTP_LENGTH - 1) {
      const nextInput = document.getElementById("otp-" + (index + 1));
      nextInput?.focus();
    }

    // Auto-submit when all digits entered
    if (value && index === OTP_LENGTH - 1) {
      const fullOtp = next.join("");
      if (fullOtp.length === OTP_LENGTH) handleVerify(fullOtp);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.getElementById("otp-" + (index - 1));
      prevInput?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, OTP_LENGTH);
    if (!pasted) return;
    const next = [...otp];
    pasted.split("").forEach((char, i) => { if (i < OTP_LENGTH) next[i] = char; });
    setOtp(next);
    if (pasted.length === OTP_LENGTH) handleVerify(pasted);
  };

  const handleVerify = async (code: string) => {
    setLoading(true); setError("");
    try {
      const ok = await login("http://localhost:8000/api/v1", "mfa-token-" + code);
      if (!ok) setError("Invalid verification code. Please try again.");
    } catch {
      setError("Verification failed. Please try again.");
    }
    setLoading(false);
  };

  const handleResend = useCallback(() => {
    setCanResend(false);
    setCountdown(RESEND_COOLDOWN);
    setError("");
    setOtp(Array(OTP_LENGTH).fill(""));
    document.getElementById("otp-0")?.focus();
  }, []);

  const isComplete = otp.every((d) => d !== "");

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-app relative">
      {/* Full-screen Background Image */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: 'url(/images/mfa-bg.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />

      {/* MFA Card */}
      <div className="relative z-10 w-full max-w-[684px] px-6">
        <Card className="shadow-modal border-border-default">
          <CardHeader className="text-center pb-2">
            <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-primary-50 mx-auto mb-4">
              <Lock className="w-7 h-7 text-primary-600" />
            </div>
            <CardTitle className="text-h2 text-text-strong">Two-Factor Authentication</CardTitle>
            <CardDescription className="text-caption text-text-muted mt-2">
              Enter the 6-digit verification code sent to your registered device
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6 pt-2">
            {/* OTP Inputs */}
            <div className="flex justify-center gap-[18px]" onPaste={handlePaste}>
              {otp.map((digit, i) => (
                <input
                  key={i}
                  id={"otp-" + i}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpChange(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  className={"w-14 h-16 text-center text-[22px] font-bold rounded-xl border-2 bg-bg-surface-tint transition-all outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 " + (digit ? "border-primary-500 text-text-strong" : "border-border-default text-text-muted")}
                  disabled={loading}
                  autoFocus={i === 0}
                />
              ))}
            </div>

            {/* Error message */}
            {error && (
              <div className="flex items-center justify-center gap-2 p-3 rounded-lg bg-danger-50 border border-danger-100">
                <Shield className="w-4 h-4 text-danger-500 flex-shrink-0" />
                <p className="text-[13px] text-danger-600">{error}</p>
              </div>
            )}

            {/* Verify button */}
            <Button
              className="w-full h-12 text-[14px] font-semibold gap-2"
              disabled={!isComplete || loading}
              onClick={() => handleVerify(otp.join(""))}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
              {loading ? "Verifying..." : "Verify Code"}
            </Button>

            {/* Resend & Back */}
            <div className="flex items-center justify-between text-[13px]">
              <button
                onClick={handleResend}
                disabled={!canResend}
                className={"font-medium transition-colors " + (canResend ? "text-primary-600 hover:text-primary-700" : "text-text-subtle cursor-not-allowed")}
              >
                {canResend ? "Resend code" : "Resend in " + countdown + "s"}
              </button>
              <button
                onClick={() => router.back()}
                className="flex items-center gap-1 text-text-muted hover:text-text-default transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to sign in
              </button>
            </div>

            {/* Trust Strip */}
            <div className="flex justify-center gap-6 pt-4 border-t border-border-subtle">
              <span className="text-[12px] text-text-muted flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-success-600" /> HIPAA Compliant
              </span>
              <span className="text-[12px] text-text-muted flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5 text-success-600" /> SOC 2 Type II
              </span>
              <span className="text-[12px] text-text-muted flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-success-600" /> Audit Logged
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
