import { Shield, ShieldAlert } from "lucide-react";

interface ContextChipProps {
  fullName: string;
  mrn: string;
  permission?: "full" | "limited" | "denied";
  onRemove?: () => void;
  size?: "sm" | "md";
}

export function ContextChip({ fullName, mrn, permission = "full", onRemove, size = "md" }: ContextChipProps) {
  const initials = fullName.split(" ").map((n) => n[0]).join("").toUpperCase();
  const isSm = size === "sm";

  return (
    <div className={"inline-flex items-center gap-2 bg-bg-surface-tint border border-border-subtle rounded-lg " + (isSm ? "px-2.5 py-1.5" : "px-3 py-2")}>
      <div className={(isSm ? "w-6 h-6" : "w-8 h-8") + " rounded-full bg-primary-100 text-primary-700 flex items-center justify-center " + (isSm ? "text-[10px]" : "text-[12px]") + " font-semibold flex-shrink-0"}>
        {initials}
      </div>
      <div className="flex flex-col min-w-0">
        <span className={(isSm ? "text-[12px]" : "text-[13px]") + " font-medium text-text-default truncate"}>{fullName}</span>
        <span className="text-[11px] text-text-muted">MRN: {mrn}</span>
      </div>
      {permission === "limited" && (
        <ShieldAlert className="w-3.5 h-3.5 text-warning-500 flex-shrink-0" />
      )}
      {permission === "denied" && (
        <Shield className="w-3.5 h-3.5 text-danger-600 flex-shrink-0" />
      )}
      {onRemove && (
        <button onClick={onRemove} className="ml-1 text-text-subtle hover:text-text-muted transition-colors">
          ×
        </button>
      )}
    </div>
  );
}
