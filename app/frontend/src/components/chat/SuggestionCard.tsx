import { LucideIcon } from "lucide-react";

interface SuggestionCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  onClick?: () => void;
}

export function SuggestionCard({ icon: Icon, title, description, onClick }: SuggestionCardProps) {
  return (
    <button onClick={onClick} className="flex items-start gap-3 p-4 bg-bg-surface-tint rounded-xl border border-border-subtle hover:border-primary-200 hover:shadow-card transition-all text-left group">
      <span className="w-10 h-10 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0 group-hover:bg-primary-100 transition-colors">
        <Icon className="w-5 h-5 text-primary-600" />
      </span>
      <div>
        <p className="text-[14px] font-semibold text-text-default mb-0.5">{title}</p>
        <p className="text-[12px] text-text-muted leading-relaxed">{description}</p>
      </div>
    </button>
  );
}
