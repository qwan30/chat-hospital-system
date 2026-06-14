"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Eye, EyeOff, Check } from "lucide-react";
import { useRouter } from "next/navigation";

export function LoginCard() {
  const { login, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSSOLogin = async () => {
    setLoading(true);
    setError("");
    const ok = await login("http://localhost:8000/api/v1", "dev-admin");
    if (!ok) setError("SSO authentication failed.");
    setLoading(false);
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password.");
      setLoading(false);
      return;
    }
    const ok = await login("http://localhost:8000/api/v1", password.trim());
    if (ok) {
      router.push("/login/mfa"); // Redirect to MFA step
    } else {
      setError("Invalid email or password.");
    }
    setLoading(false);
  };

  return (
    <div className="w-full flex flex-col pt-12 pb-16">
      <h2 className="text-[24px] font-bold text-text-strong mb-1">Welcome back</h2>
      <p className="text-[12px] text-text-muted mb-8">Sign in to your AI-Powered Hospital Knowledge Assistant</p>

      {/* SSO Button */}
      <button 
        onClick={handleSSOLogin} 
        disabled={loading}
        className="flex items-center justify-center gap-2 w-full h-14 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-[14px] font-bold transition-colors"
      >
        <Shield className="w-4 h-4" />
        Sign in with Hospital SSO
      </button>

      <div className="flex items-center my-6">
        <div className="flex-1 border-t border-border-default"></div>
        <span className="px-4 text-[11px] text-text-subtle">or continue with email</span>
        <div className="flex-1 border-t border-border-default"></div>
      </div>

      {/* Email/Password Form */}
      <form onSubmit={handleEmailLogin} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-[13px] font-bold text-text-strong">Email address</Label>
          <Input 
            id="email" 
            type="email" 
            placeholder="Enter your email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            className="h-12 border-border-default rounded-xl bg-white px-4 placeholder:text-text-subtle" 
            required 
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-[13px] font-bold text-text-strong">Password</Label>
          <div className="relative">
            <Input 
              id="password" 
              type={showPassword ? "text" : "password"} 
              placeholder="Enter your password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              className="h-12 border-border-default rounded-xl bg-white px-4 pr-10 placeholder:text-text-subtle" 
              required 
            />
            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-text-subtle hover:text-text-muted">
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {error && <p className="text-[13px] text-danger-600">{error}</p>}

        <div className="flex items-center justify-between mt-2">
          <label className="flex items-center gap-2 text-[13px] text-text-default cursor-pointer">
            <input type="checkbox" className="w-4 h-4 rounded border-border-default text-primary-600 focus:ring-primary-500" />
            Remember this device
          </label>
          <a href="#" className="text-[13px] font-bold text-primary-600 hover:text-primary-700">Forgot password?</a>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          className="flex items-center justify-center w-full h-14 bg-primary-50 hover:bg-primary-100 text-primary-600 rounded-xl text-[14px] font-bold transition-colors mt-2"
        >
          Sign in with email
        </button>
      </form>

      {/* Security Box */}
      <div className="mt-8 p-4 bg-success-50 rounded-xl border border-success-100 flex flex-col gap-3">
        <div className="flex gap-4 items-start">
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-success-100 flex-shrink-0">
            <Shield className="w-5 h-5 text-success-700" />
          </div>
          <div className="flex flex-col">
            <h4 className="text-[13px] font-bold text-success-700 mb-0.5">Secure access. Your data is protected.</h4>
            <p className="text-[11px] text-text-muted">This system is designed to protect PHI and comply with HIPAA requirements. All access is monitored and audit-logged.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-4 ml-14">
          {["PHI Protection", "Audit Logging", "Role-Based Access"].map((t) => (
            <span key={t} className="text-[11px] font-bold text-success-700 flex items-center gap-1">
              <Check className="w-3 h-3" /> {t}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-12 text-center text-[12px] text-text-subtle">
        Need help? Contact your IT administrator
        <div className="mt-2 text-[11px]">
          © 2026 AI-Powered Hospital Knowledge Assistant. All rights reserved.
        </div>
      </div>
    </div>
  );
}
