import type { ReactNode } from "react";
import { Wordmark } from "@/components/hms/Logo";
import { ShieldCheck, Lock, Eye, Stethoscope } from "lucide-react";
import backgroundLeftLogin from "@/assets/background-left-login.png";

export function AuthSplitLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen w-full bg-background lg:grid-cols-[1.1fr_1fr]">
      <div className="relative hidden flex-col justify-between overflow-hidden p-10 lg:flex text-slate-900 border-r border-border bg-slate-50">
        <img
          src={backgroundLeftLogin}
          alt=""
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 right-0 h-full w-full object-cover object-[10%_center] animate-in fade-in duration-300"
        />
        {/* Soft transition gradient from solid slate-50 to transparent */}
        <div className="absolute inset-y-0 right-0 w-[30%] bg-gradient-to-l from-slate-50 via-slate-50/60 to-transparent pointer-events-none" />

        <div className="relative">
          <Wordmark />
          <h1 className="mt-12 max-w-md text-4xl font-semibold leading-tight tracking-tight text-slate-900">
            Smarter insights.
            <br />
            Better patient care.
          </h1>
          <p className="mt-3 max-w-md text-sm text-slate-600 font-medium">
            HMS AI Copilot is your hospital's evidence-first knowledge assistant — cited,
            permission-aware, and built for clinicians.
          </p>
        </div>
        <div className="relative grid max-w-md grid-cols-2 gap-3 text-sm">
          {[
            { icon: ShieldCheck, t: "Enterprise security", d: "SOC 2 · HIPAA aligned" },
            { icon: Lock, t: "PHI-safe", d: "Local-first retrieval" },
            { icon: Eye, t: "Cited answers", d: "Every claim traceable" },
            { icon: Stethoscope, t: "Built for clinicians", d: "Clinical workflows first" },
          ].map((f) => (
            <div
              key={f.t}
              className="rounded-xl border border-slate-200 bg-white/75 p-3 backdrop-blur-xs shadow-xs text-slate-800"
            >
              <f.icon className="h-4 w-4 text-primary" />
              <p className="mt-2 font-semibold text-slate-900">{f.t}</p>
              <p className="text-xs text-slate-500 font-medium">{f.d}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
