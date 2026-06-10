import { AlertTriangle } from "lucide-react";

export function LowConfidenceBanner({ count = 0 }: { count?: number }) {
  if (count === 0) return null;
  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-warning-50 border border-warning-100">
      <AlertTriangle className="w-4 h-4 text-warning-500 flex-shrink-0" />
      <p className="text-[13px] text-warning-700">{count} section{count !== 1 ? "s" : ""} with low OCR confidence. Manual review recommended.</p>
    </div>
  );
}
