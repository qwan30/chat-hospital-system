import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ArrowDownRight, ArrowUpRight, type LucideIcon } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";

export interface MetricCardProps {
  label: string;
  value: string;
  delta?: { value: string; positive?: boolean };
  icon?: LucideIcon;
  tone?: "primary" | "secondary" | "ai" | "citation" | "warning";
  spark?: number[];
}

const toneColor: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  primary: "var(--color-primary)",
  secondary: "var(--color-secondary)",
  ai: "var(--color-ai)",
  citation: "var(--color-citation)",
  warning: "var(--color-warning)",
};

export function MetricCard({
  label,
  value,
  delta,
  icon: Icon,
  tone = "primary",
  spark,
}: MetricCardProps) {
  const color = toneColor[tone];
  const data = (spark ?? []).map((v, i) => ({ i, v }));
  return (
    <Card className="relative overflow-hidden p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {label}
          </p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
        </div>
        {Icon ? (
          <div
            className="flex h-9 w-9 items-center justify-center rounded-lg"
            style={{ backgroundColor: `${color}1A`, color }}
          >
            <Icon className="h-4.5 w-4.5" />
          </div>
        ) : null}
      </div>
      {delta ? (
        <div className="mt-3 flex items-center gap-1 text-xs">
          <span
            className={cn(
              "inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 font-medium",
              delta.positive ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive",
            )}
          >
            {delta.positive ? (
              <ArrowUpRight className="h-3 w-3" />
            ) : (
              <ArrowDownRight className="h-3 w-3" />
            )}
            {delta.value}
          </span>
          <span className="text-muted-foreground">vs last week</span>
        </div>
      ) : null}
      {spark && spark.length > 0 ? (
        <div className="mt-3 h-10">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={`g-${label}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="v"
                stroke={color}
                strokeWidth={1.8}
                fill={`url(#g-${label})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </Card>
  );
}
