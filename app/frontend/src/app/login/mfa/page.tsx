"use client";

import { useAuth } from "@/lib/auth-context";
import { MFACard } from "@/components/auth/MFACard";
import { Shield } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function MFAPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If not authenticated or no ongoing session, one could redirect back to login,
    // but for the sake of UI preview, we'll allow it.
    if (isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, authLoading, router]);

  if (isAuthenticated || authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-app">
        <p className="text-text-muted">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-app flex flex-col relative items-center justify-center py-12 px-4">
      {/* Top right pills */}
      <div className="absolute top-8 right-8 flex flex-col gap-2 z-20 items-end">
        <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-success-50 border border-success-100 shadow-sm">
          <span className="w-4 h-4 rounded-sm bg-success-600 flex items-center justify-center text-white text-[10px]">DB</span>
          <span className="text-[12px] text-success-700">Synthetic Data</span>
        </div>
      </div>

      <div className="w-full max-w-[684px] flex flex-col items-center z-10">
        
        {/* Brand Lockup above card */}
        <div className="mb-8 flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-xl shadow-sm text-white font-bold text-lg">
            H
          </div>
          <div className="flex flex-col">
            <span className="text-body-strong text-text-strong">AI-Powered Hospital</span>
            <span className="text-caption text-text-muted">Knowledge Assistant</span>
          </div>
        </div>

        <MFACard />

        {/* 3 Marketing Blocks below card */}
        <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 px-8">
          <div className="flex flex-col">
            <h4 className="text-[12px] font-bold text-text-strong mb-1">Your data is protected</h4>
            <p className="text-[11px] text-text-muted leading-relaxed">We use enterprise-grade encryption to keep patient data secure.</p>
          </div>
          <div className="flex flex-col">
            <h4 className="text-[12px] font-bold text-text-strong mb-1">MFA for stronger security</h4>
            <p className="text-[11px] text-text-muted leading-relaxed">Multi-factor authentication helps protect your account.</p>
          </div>
          <div className="flex flex-col">
            <h4 className="text-[12px] font-bold text-text-strong mb-1">Audit-ready access</h4>
            <p className="text-[11px] text-text-muted leading-relaxed">All access attempts are logged and monitored for compliance.</p>
          </div>
        </div>

        {/* Footer links */}
        <div className="mt-16 text-center text-[11px] text-text-subtle">
          <Link href="#" className="hover:text-text-muted transition-colors">Need help? Contact IT Support ↗</Link>
          <span className="mx-2">|</span>
          <Link href="/login" className="hover:text-text-muted transition-colors">Return to sign in</Link>
        </div>
      </div>
    </div>
  );
}
