import { SuggestionCard } from "./SuggestionCard";
import { FileSearch, Pill, Activity, ClipboardCheck, Heart, AlertTriangle } from "lucide-react";

const PROMPTS = [
  { icon: FileSearch, title: "Summarize recent labs", description: "Get an AI summary of the latest lab results with trend analysis" },
  { icon: Pill, title: "Review medications", description: "Check current medications for interactions and contraindications" },
  { icon: Activity, title: "Assess vitals trend", description: "Analyze vital signs over the last 48 hours" },
  { icon: ClipboardCheck, title: "Pre-round summary", description: "Generate a concise pre-rounding summary for this patient" },
  { icon: Heart, title: "Cardiac risk review", description: "Evaluate cardiovascular risk factors and recommendations" },
  { icon: AlertTriangle, title: "Flag abnormal results", description: "Identify and explain any out-of-range lab values" },
];

interface PromptGridProps {
  onSelect?: (prompt: string) => void;
}

export function PromptGrid({ onSelect }: PromptGridProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {PROMPTS.map((p) => (
        <SuggestionCard key={p.title} icon={p.icon} title={p.title} description={p.description} onClick={() => onSelect?.(p.title)} />
      ))}
    </div>
  );
}
