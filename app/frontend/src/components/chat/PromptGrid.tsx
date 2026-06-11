import { LucideIcon } from "lucide-react";
import { SuggestionCard } from "./SuggestionCard";
import { FileSearch, Pill, Activity, ClipboardCheck, Heart, AlertTriangle } from "lucide-react";

export interface Prompt {
  icon: LucideIcon;
  title: string;
  description: string;
}

interface PromptGridProps {
  prompts?: Prompt[];
  onSelect?: (prompt: Prompt) => void;
}

const DEFAULT_PROMPTS: Prompt[] = [
  { icon: FileSearch, title: "Summarize recent labs", description: "Get an AI summary of the latest lab results with trend analysis" },
  { icon: Pill, title: "Review medications", description: "Check current medications for interactions and contraindications" },
  { icon: Activity, title: "Assess vitals trend", description: "Analyze vital signs over the last 48 hours" },
  { icon: ClipboardCheck, title: "Pre-round summary", description: "Generate a concise pre-rounding summary for this patient" },
  { icon: Heart, title: "Cardiac risk review", description: "Evaluate cardiovascular risk factors and recommendations" },
  { icon: AlertTriangle, title: "Flag abnormal results", description: "Identify and explain any out-of-range lab values" },
];

export function PromptGrid({ prompts, onSelect }: PromptGridProps) {
  const items = prompts || DEFAULT_PROMPTS;

  return (
    <div className="grid grid-cols-2 gap-3">
      {items.map((p) => (
        <SuggestionCard key={p.title} icon={p.icon} title={p.title} description={p.description} onClick={() => onSelect?.(p)} />
      ))}
    </div>
  );
}
