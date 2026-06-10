import { Upload, Scan, Search, CheckCircle } from "lucide-react";

const STEPS = [
  { icon: Upload, label: "Uploaded", date: "May 15, 2025 8:30 AM" },
  { icon: Scan, label: "OCR Processing", date: "May 15, 2025 8:32 AM" },
  { icon: Search, label: "Review", date: "May 15, 2025 8:45 AM" },
  { icon: CheckCircle, label: "Indexed", date: "Pending" },
];

export function ProcessingTimeline() {
  return (
    <div className="relative pl-6 space-y-4">
      <div className="absolute left-2 top-2 bottom-2 w-px bg-border-subtle" />
      {STEPS.map((s, i) => (
        <div key={i} className="relative flex items-start gap-3">
          <span className={"absolute -left-6 w-4 h-4 rounded-full border-2 flex items-center justify-center " + (i < 3 ? "bg-success-50 border-success-500" : "bg-bg-surface-tint border-border-subtle")}>
            {i < 3 ? <CheckCircle className="w-2.5 h-2.5 text-success-500" /> : <s.icon className="w-2.5 h-2.5 text-text-subtle" />}
          </span>
          <div><p className="text-[13px] font-medium text-text-default">{s.label}</p><p className="text-[11px] text-text-subtle">{s.date}</p></div>
        </div>
      ))}
    </div>
  );
}
