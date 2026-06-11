"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Shield, Mail, Lock, Eye, EyeOff } from "lucide-react";


export default function LoginPage() {
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && isAuthenticated) router.replace("/dashboard");
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || isAuthenticated) return <div className="min-h-screen flex items-center justify-center bg-bg-app"><p className="text-text-muted">Loading...</p></div>;

  const handleSSOLogin = async () => {
    setLoading(true); setError("");
    const ok = await login("http://localhost:8000/api/v1", "dev-doctor");
    if (!ok) setError("SSO authentication failed.");
    setLoading(false);
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true); setError("");
    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and access token.");
      setLoading(false);
      return;
    }
    const ok = await login("http://localhost:8000/api/v1", password.trim());
    if (!ok) setError("Invalid email or access token.");
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex bg-bg-app relative">
      {/* Environment Pill — top right */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/90 border border-border-subtle shadow-sm">
        <span className="w-2 h-2 rounded-full bg-success-600" />
        <span className="text-[11px] font-medium text-text-muted">Synthetic Data</span>
      </div>

      {/* Background Image — left marketing pane only */}
      <div
        className="absolute inset-y-0 left-0 z-0 w-[45%] hidden lg:block"
        style={{
          backgroundImage: 'url(/images/login-bg.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />

      {/* Marketing Pane */}
      <div className="relative z-10 hidden lg:flex w-[45%] flex-col justify-start pt-16 px-14 text-white bg-gradient-to-br from-primary-700/90 via-primary-600/70 to-primary-500/50 backdrop-blur-[2px]">
        <div className="mb-8">
          <img src="/images/logo.png" alt="Hospital AI" className="w-12 h-12 mb-6" />
          <h1 className="text-display mb-3">AI-Powered Hospital Knowledge Assistant</h1>
          <p className="text-white/80 text-[16px] leading-relaxed">Access clinical knowledge, patient summaries, and cited answers — all in one place.</p>
        </div>
        <div className="space-y-4">
          {[
            { icon: Shield, text: "HIPAA-compliant, role-based access control" },
            { icon: Lock, text: "End-to-end encrypted data transmission" },
            { icon: Shield, text: "Complete audit logging on every action" },
            { icon: Lock, text: "AI answers with verified clinical citations" },
          ].map((f, i) => (
            <div key={i} className="flex items-center gap-3">
              <f.icon className="w-5 h-5 text-white/70 flex-shrink-0" />
              <span className="text-[14px] text-white/90">{f.text}</span>
            </div>
          ))}
        </div>
        {/* Trust footnote */}
        <p className="mt-auto mb-8 text-[12px] text-white/60">HIPAA Compliant &bull; SOC 2 Type II &bull; Enterprise Ready</p>
      </div>

      {/* Form Pane */}
      <div
        className="relative z-10 flex-1 flex items-center justify-center px-8 bg-gradient-to-br from-primary-50/50 to-bg-surface"
        style={{
          backgroundImage: 'url(/images/login-right-bg.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="relative z-10 w-full max-w-[440px]">
        <Card className="w-full max-w-[440px] shadow-modal bg-white/95">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-h2 text-text-strong">Welcome back</CardTitle>
            <CardDescription className="text-caption text-text-muted mt-1">Sign in to your hospital account</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            {/* SSO Button */}
            <Button variant="outline" className="w-full h-11 gap-2 text-[14px] font-semibold" onClick={handleSSOLogin} disabled={loading}>
              <Shield className="w-4 h-4" />
              Sign in with Hospital SSO
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border-subtle" /></div>
              <div className="relative flex justify-center text-[12px]"><span className="bg-bg-surface px-3 text-text-muted">or continue with email</span></div>
            </div>

            {/* Email/Password Form */}
            <form onSubmit={handleEmailLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
                  <Input id="email" type="email" placeholder="Enter your email" value={email} onChange={(e) => setEmail(e.target.value)} className="pl-10" required />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Access Token</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
                  <Input id="password" type={showPassword ? "text" : "password"} placeholder="Enter dev token (e.g. dev-doctor)" value={password} onChange={(e) => setPassword(e.target.value)} className="pl-10 pr-10" required />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-subtle hover:text-text-muted">
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              {error && <p className="text-[13px] text-danger-600">{error}</p>}
              {/* Remember me + Forgot password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-[13px] text-text-muted cursor-pointer">
                  <input type="checkbox" className="rounded border-border-default" />
                  Remember me
                </label>
                <a href="#" className="text-[13px] text-text-link hover:underline">Forgot password?</a>
              </div>
              <Button type="submit" className="w-full h-11 text-[14px] font-semibold" disabled={loading}>
                Sign in with email
              </Button>
            </form>

            {/* Trust badges */}
            <div className="flex justify-center gap-4 pt-2">
              {["PHI Protection", "Audit Logging", "Role-Based Access"].map((t) => (
                <span key={t} className="text-[11px] text-text-muted flex items-center gap-1">
                  <Shield className="w-3 h-3 text-success-600" /> {t}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}
