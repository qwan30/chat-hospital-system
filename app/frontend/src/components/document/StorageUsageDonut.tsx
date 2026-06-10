import { HardDrive } from "lucide-react";

interface StorageUsageDonutProps {
  usedGB: number;
  totalGB: number;
}

export function StorageUsageDonut({ usedGB, totalGB }: StorageUsageDonutProps) {
  const pct = Math.round((usedGB / totalGB) * 100);
  return (
    <div className="flex flex-col items-center p-4 bg-bg-surface-tint rounded-xl border border-border-subtle">
      <div className="relative w-24 h-24 mb-2">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          <circle cx="18" cy="18" r="14" fill="none" stroke="#EEF3FB" strokeWidth="4" />
          <circle cx="18" cy="18" r="14" fill="none" stroke="#2F7AF7" strokeWidth="4" strokeDasharray={88 * pct / 100 + " " + 88 * (100 - pct) / 100} strokeLinecap="round" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center"><HardDrive className="w-5 h-5 text-primary-500" /></div>
      </div>
      <p className="text-[14px] font-bold text-text-default">{usedGB} GB</p>
      <p className="text-[11px] text-text-subtle">of {totalGB} GB used</p>
    </div>
  );
}
