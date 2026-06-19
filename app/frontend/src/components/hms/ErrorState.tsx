import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";

export function ErrorState({
  code,
  title,
  description,
  cta,
  tone = "warning",
  extra,
}: {
  code: string;
  title: string;
  description: string;
  cta?: { label: string; to: string };
  tone?: "warning" | "critical" | "info";
  extra?: ReactNode;
}) {
  const toneCls: Record<string, string> = {
    warning: "border-warning/40 bg-warning/5 text-warning",
    critical: "border-destructive/40 bg-destructive/5 text-destructive",
    info: "border-info/40 bg-info/5 text-info",
  };
  return (
    <div className="mx-auto flex min-h-[calc(100vh-2rem)] max-w-xl items-center px-6 py-10">
      <Card className="w-full p-8">
        <div
          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${toneCls[tone]}`}
        >
          <span>{code}</span>
        </div>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
        {extra ? <div className="mt-4">{extra}</div> : null}
        <div className="mt-6 flex flex-wrap gap-2">
          {cta ? (
            <Button asChild>
              <Link to={cta.to}>{cta.label}</Link>
            </Button>
          ) : null}
          <Button asChild variant="outline">
            <Link to="/dashboard">Back to dashboard</Link>
          </Button>
        </div>
        <p className="mt-6 text-xs text-muted-foreground">
          Audit event logged · ref{" "}
          <span className="font-mono text-foreground">
            evt-{code.toLowerCase().replace(/\s+/g, "-")}-7421
          </span>
        </p>
      </Card>
    </div>
  );
}
