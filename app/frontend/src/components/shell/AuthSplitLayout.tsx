import type { ReactNode } from "react";
import { Wordmark } from "@/components/hms/Logo";
import { ShieldCheck, Lock, Eye, Stethoscope } from "lucide-react";
import authHero from "@/assets/auth-hero.png.asset.json";

export function AuthSplitLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen w-full bg-background lg:grid-cols-[1.1fr_1fr]">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-linear-to-br from-primary via-primary to-ai p-10 text-primary-foreground lg:flex">
        <img
          src={authHero.url}
          alt=""
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-60 mix-blend-screen"
        />
        <div className="absolute inset-0 bg-linear-to-br from-primary/70 via-primary/40 to-ai/60" />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, white 0, transparent 40%), radial-gradient(circle at 80% 60%, white 0, transparent 35%)",
          }}
        />
        <div className="relative">
          <Wordmark className="[&_span]:text-primary-foreground" />
          <h1 className="mt-12 max-w-md text-4xl font-semibold leading-tight tracking-tight">
            Smarter insights.
            <br />
            Better patient care.
          </h1>
          <p className="mt-3 max-w-md text-sm text-primary-foreground/80">
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
              className="rounded-xl border border-white/15 bg-white/10 p-3 backdrop-blur"
            >
              <f.icon className="h-4 w-4" />
              <p className="mt-2 font-medium">{f.t}</p>
              <p className="text-xs text-primary-foreground/70">{f.d}</p>
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