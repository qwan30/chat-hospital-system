import { Database } from "lucide-react";

export function SyntheticDataPill() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-warning/30 bg-warning/10 px-2.5 py-1 text-xs font-medium text-warning">
      <Database className="h-3 w-3" />
      Synthetic Data
    </span>
  );
}