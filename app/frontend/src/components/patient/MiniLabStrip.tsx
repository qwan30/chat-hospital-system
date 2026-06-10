import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface LabValue {
  label: string;
  value: string;
  unit: string;
  trend?: "up" | "down" | "stable";
  status?: "normal" | "high" | "low" | "critical";
  referenceRange?: string;
}

interface MiniLabStripProps {
  labs: LabValue[];
}

const STATUS_COLORS: Record<string, string> = {
  normal: "text-success-600",
  high: "text-warning-500",
  low: "text-primary-600",
  critical: "text-danger-600",
};

const TREND_ICONS = {
  up: TrendingUp,
  down: TrendingDown,
  stable: Minus,
};

const TREND_COLORS: Record<string, string> = {
  up: "text-warning-500",
  down: "text-success-600",
  stable: "text-text-subtle",
};

export function MiniLabStrip({ labs }: MiniLabStripProps) {
  return (
    <div className="flex items-center gap-4 overflow-x-auto pb-2">
      {labs.map((lab) => {
        const TrendIcon = lab.trend ? TREND_ICONS[lab.trend] : null;
        const trendColor = lab.trend ? TREND_COLORS[lab.trend] : "";
        const statusColor = lab.status ? STATUS_COLORS[lab.status] : "";

        return (
          <div
            key={lab.label}
            className="flex-shrink-0 flex flex-col items-center gap-1 px-4 py-3 bg-bg-surface-tint rounded-lg border border-border-subtle min-w-[100px]"
          >
            <span className="text-[11px] text-text-subtle font-medium">{lab.label}</span>
            <div className="flex items-center gap-1.5">
              <span className={"text-[18px] font-bold " + (statusColor || "text-text-strong")}>
                {lab.value}
              </span>
              {TrendIcon && <TrendIcon className={"w-3.5 h-3.5 " + trendColor} />}
            </div>
            <span className="text-[10px] text-text-subtle">{lab.unit}</span>
            {lab.referenceRange && (
              <span className="text-[10px] text-text-subtle">Ref: {lab.referenceRange}</span>
            )}
          </div>
        );
      })}
    </div>
  );
}
