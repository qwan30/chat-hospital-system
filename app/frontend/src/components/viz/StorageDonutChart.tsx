import { HardDrive } from "lucide-react";

export function StorageDonutChart({ used = 12.4, total = 50, label = "Document Storage" }: { used?: number; total?: number; label?: string }) {
  const pct = Math.round((used / total) * 100);
  return (
    <div className="flex flex-col items-center p-6 bg-bg-surface-tint rounded-xl border border-border-subtle">
      <div className="relative w-28 h-28 mb-3">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90"><circle cx="18" cy="18" r="14" fill="none" stroke="#EEF3FB" strokeWidth="3" /><circle cx="18" cy="18" r="14" fill="none" stroke="#2F7AF7" strokeWidth="3" strokeDasharray={(87.96 * pct / 100).toFixed(1) + " " + (87.96 * (100 - pct) / 100).toFixed(1)} strokeLinecap="round" /></svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center"><span className="text-[18px] font-bold text-text-strong">{pct}%</span><span className="text-[10px] text-text-subtle">used</span></div>
      </div>
      <p className="text-[13px] text-text-muted">{label}</p>
      <p className="text-[11px] text-text-subtle">{used} GB of {total} GB</p>
    </div>
  );
}
