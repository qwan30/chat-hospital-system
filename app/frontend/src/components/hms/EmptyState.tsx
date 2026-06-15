import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  actions,
  className,
  tone = "muted",
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
  tone?: "muted" | "info" | "warning" | "critical" | "ai";
}) {
  const toneCls: Record<string, string> = {
    muted: "bg-muted text-muted-foreground",
    info: "bg-info/10 text-info",
    warning: "bg-warning/10 text-warning",
    critical: "bg-destructive/10 text-destructive",
    ai: "bg-ai/10 text-ai",
  };
  return (
    <Card className={cn("flex flex-col items-center justify-center gap-3 p-10 text-center", className)}>
      {Icon ? (
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-full", toneCls[tone])}>
          <Icon className="h-6 w-6" />
        </div>
      ) : null}
      <div>
        <div className="text-base font-semibold">{title}</div>
        {description ? (
          <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="mt-2 flex flex-wrap items-center justify-center gap-2">{actions}</div> : null}
    </Card>
  );
}