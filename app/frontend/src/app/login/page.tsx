"use client";

import { useState } from "react";
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

  if (authLoading) return <div className="min-h-screen flex items-center justify-center bg-bg-app"><p className="text-text-muted">Loading...</p></div>;
  if (isAuthenticated) { router.replace("/dashboard"); return null; }

  const handleSSOLogin = async () => {
    setLoading(true); setError("");
    const ok = await login("http://localhost:8000/api/v1", "sso-token-placeholder");
    if (!ok) setError("SSO authentication failed.");
    setLoading(false);
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true); setError("");
    const ok = await login("http://localhost:8000/api/v1", "email-token-placeholder");
    if (!ok) setError("Invalid email or password.");
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex bg-bg-app relative">
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
      <div className="relative z-10 hidden lg:flex w-[45%] flex-col justify-center px-16 text-white">
        <div className="mb-8">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-white/20 text-white font-bold text-xl mb-6">H</div>
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
      </div>

      {/* Form Pane with background */}
      <div
        className="relative z-10 flex-1 flex items-center justify-center px-8"
        style={{
          backgroundImage: 'url(/images/login-right-bg.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="absolute inset-0 bg-white/70 backdrop-blur-sm" />
        <div className="relative z-10 w-full max-w-[440px]">
        <Card className="w-full max-w-[440px] shadow-card">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-h2 text-text-strong">Welcome back</CardTitle>
            <CardDescription className="text-caption text-text-muted mt-1">Sign in to your hospital account</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 pt-4">
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
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
                  <Input id="password" type={showPassword ? "text" : "password"} placeholder="Enter password" value={password} onChange={(e) => setPassword(e.target.value)} className="pl-10 pr-10" required />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-subtle hover:text-text-muted">
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              {error && <p className="text-[13px] text-danger-600">{error}</p>}
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
