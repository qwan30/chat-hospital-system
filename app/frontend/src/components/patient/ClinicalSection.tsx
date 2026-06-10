import { Stethoscope, Activity, Heart, Brain, Pill } from "lucide-react";

const SECTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  "Chief Complaint": Stethoscope,
  "History of Present Illness": Activity,
  "Vital Signs": Heart,
  "Assessment": Brain,
  "Plan": Pill,
};

interface ClinicalSectionProps {
  title: string;
  content: string;
  citations?: number[];
  onCitationClick?: (citationId: number) => void;
}

export function ClinicalSection({ title, content, citations, onCitationClick }: ClinicalSectionProps) {
  const Icon = SECTION_ICONS[title] || Activity;

  return (
    <div className="py-3 border-b border-border-subtle last:border-0">
      <div className="flex items-start gap-3">
        <span className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Icon className="w-4 h-4 text-primary-600" />
        </span>
        <div className="flex-1 min-w-0">
          <h4 className="text-[14px] font-semibold text-text-default mb-1">{title}</h4>
          <p className="text-body text-text-default leading-relaxed">
            {content}
            {citations && citations.map((id) => (
              <button
                key={id}
                onClick={() => onCitationClick && onCitationClick(id)}
                className="inline-flex items-center px-1 ml-0.5 text-[11px] font-semibold text-primary-600 bg-primary-50 rounded hover:bg-primary-100 transition-colors"
              >
                [{id}]
              </button>
            ))}
          </p>
        </div>
      </div>
    </div>
  );
}
