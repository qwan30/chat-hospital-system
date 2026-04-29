/**
 * Confidence indicator badge for AI responses.
 *
 * Displays a color-coded confidence level with an icon,
 * inspired by Kotaemon's QA confidence score display.
 */

import { AlertTriangle, CheckCircle2, HelpCircle, ShieldCheck } from "lucide-react";

type ConfidenceLevel = "high" | "medium" | "low" | "unknown";

const confidenceConfig: Record<
  ConfidenceLevel,
  {
    label: string;
    icon: typeof CheckCircle2;
    className: string;
    description: string;
  }
> = {
  high: {
    label: "High confidence",
    icon: ShieldCheck,
    className: "border-[#34d399]/40 bg-[#34d399]/10 text-[#bbf7d0]",
    description: "Strong evidence match — high retrieval scores.",
  },
  medium: {
    label: "Medium confidence",
    icon: CheckCircle2,
    className: "border-[#fbbf24]/40 bg-[#fbbf24]/10 text-[#fde68a]",
    description: "Moderate evidence match — some uncertainty.",
  },
  low: {
    label: "Low confidence",
    icon: AlertTriangle,
    className: "border-[#f87171]/40 bg-[#f87171]/10 text-[#fecaca]",
    description: "Weak evidence match — verify with primary sources.",
  },
  unknown: {
    label: "Unknown",
    icon: HelpCircle,
    className: "border-white/10 bg-white/[0.03] text-[#a3a7ad]",
    description: "Confidence could not be determined.",
  },
};

export function ConfidenceIndicator({
  confidence,
  compact = false,
}: {
  confidence: ConfidenceLevel;
  compact?: boolean;
}) {
  const config = confidenceConfig[confidence];
  const Icon = config.icon;

  if (compact) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${config.className}`}
        title={config.description}
      >
        <Icon className="size-3" />
        {config.label}
      </span>
    );
  }

  return (
    <div
      className={`flex items-start gap-2 rounded-md border px-3 py-2 ${config.className}`}
      role="status"
      aria-label={`AI response confidence: ${config.label}`}
    >
      <Icon className="mt-0.5 size-4 shrink-0" />
      <div>
        <p className="text-xs font-medium">{config.label}</p>
        <p className="mt-0.5 text-xs opacity-75">{config.description}</p>
      </div>
    </div>
  );
}
