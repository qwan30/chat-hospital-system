"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, Mail, Shield, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";

export function MFACard() {
  const router = useRouter();
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      router.push("/dashboard");
    }, 1000);
  };

  const handleInputChange = (index: number, value: string) => {
    if (value.length > 1) value = value.slice(-1);
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    if (value && index < 5) {
      document.getElementById(`otp-${index + 1}`)?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      document.getElementById(`otp-${index - 1}`)?.focus();
    }
  };

  return (
    <div className="w-full max-w-[480px] bg-white rounded-[20px] shadow-modal border border-border-default p-12">
      <div className="flex flex-col items-center text-center">
        <div className="w-16 h-16 rounded-[32px] bg-primary-100 flex items-center justify-center mb-6">
          <Lock className="w-6 h-6 text-text-strong" />
        </div>
        <h2 className="text-[22px] font-bold text-text-strong mb-2">Verify your identity</h2>
        <p className="text-[13px] text-text-default mb-6">For your security, we need to verify it&apos;s you.</p>

        {/* Email Alert Banner */}
        <div className="w-full flex items-center gap-3 bg-primary-50 rounded-lg p-3 border border-primary-100 mb-6">
          <Mail className="w-4 h-4 text-primary-600 flex-shrink-0" />
          <span className="text-[13px] text-primary-600 font-medium">We sent a 6-digit code to s***@cityviewhospital.org</span>
        </div>

        <form onSubmit={handleVerify} className="w-full flex flex-col items-center">
          <div className="w-full flex flex-col items-start mb-6">
            <label className="text-[12px] font-bold text-text-muted mb-2">Enter 6-digit code</label>
            <div className="flex justify-between w-full gap-2">
              {otp.map((digit, i) => (
                <input
                  key={i}
                  id={`otp-${i}`}
                  type="text"
                  inputMode="numeric"
                  value={digit}
                  onChange={(e) => handleInputChange(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  className="w-12 h-14 rounded-lg border border-border-default text-center text-[24px] font-bold text-text-strong focus:border-primary-600 focus:ring-1 focus:ring-primary-600 outline-none transition-all"
                  required
                />
              ))}
            </div>
          </div>

          <div className="w-full flex items-center justify-center text-[12px] mb-6">
            <span className="text-text-muted">⏱️ Code expires in 01:45</span>
            <span className="mx-3 text-border-strong">|</span>
            <button type="button" className="text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
              <span>🔄</span> Resend code
            </button>
          </div>

          <div className="w-full flex items-center my-6">
            <div className="flex-1 border-t border-border-default"></div>
            <span className="px-4 text-[13px] text-text-subtle">or</span>
            <div className="flex-1 border-t border-border-default"></div>
          </div>

          <button type="button" className="w-full h-12 flex items-center justify-between px-4 border border-border-default rounded-xl hover:bg-bg-surface-tint transition-colors mb-4">
            <div className="flex items-center gap-2 text-text-muted text-[13px]">
              <Shield className="w-4 h-4" />
              Use another method
            </div>
            <ChevronDown className="w-4 h-4 text-text-muted" />
          </button>

          <Button 
            type="submit" 
            disabled={loading || otp.join("").length < 6}
            className="w-full h-12 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-[14px] font-bold transition-colors"
          >
            Verify & Continue <span className="ml-2">➔</span>
          </Button>
        </form>
      </div>
    </div>
  );
}
