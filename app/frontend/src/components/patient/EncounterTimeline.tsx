import { Badge } from "@/components/ui/badge";
import { Stethoscope, FileText, Activity, Heart, ClipboardCheck, Pill } from "lucide-react";

interface Encounter {
  id: string;
  date: string;
  type: string;
  title: string;
  description: string;
  status: string;
}

interface EncounterTimelineProps {
  encounters: Encounter[];
}

const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  admission: Stethoscope,
  consult: FileText,
  lab: Activity,
  procedure: Heart,
  discharge: ClipboardCheck,
  medication: Pill,
};

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-success-50 text-success-600",
  active: "bg-primary-50 text-primary-600",
  pending: "bg-warning-50 text-warning-500",
  cancelled: "bg-bg-surface-tint text-text-muted",
};

export function EncounterTimeline({ encounters }: EncounterTimelineProps) {
  return (
    <div className="relative pl-8">
      <div className="absolute left-3 top-0 bottom-0 w-px bg-border-default" />
      <div className="space-y-5">
        {encounters.map((enc) => {
          const Icon = TYPE_ICONS[enc.type] || FileText;
          return (
            <div key={enc.id} className="relative">
              <span className="absolute -left-8 w-6 h-6 rounded-full bg-bg-surface border-2 border-border-default flex items-center justify-center">
                <Icon className="w-3 h-3 text-text-muted" />
              </span>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[13px] font-semibold text-text-default">{enc.title}</span>
                    <Badge variant="outline" className={STATUS_STYLES[enc.status] || STATUS_STYLES.completed}>
                      {enc.status}
                    </Badge>
                  </div>
                  <p className="text-[12px] text-text-muted">{enc.description}</p>
                </div>
                <span className="text-[11px] text-text-subtle flex-shrink-0 ml-4">{enc.date}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
