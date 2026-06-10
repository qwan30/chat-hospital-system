import { Pill, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  indication: string;
  startDate: string;
  status: string;
  citationId?: number;
  safetyConcern?: string;
}

interface MedicationListProps {
  medications: Medication[];
  onCitationClick?: (citationId: number) => void;
}

const STATUS_STYLES: Record<string, string> = {
  active: "bg-success-50 text-success-600",
  discontinued: "bg-bg-surface-tint text-text-muted",
  pending: "bg-warning-50 text-warning-500",
};

export function MedicationList({ medications, onCitationClick }: MedicationListProps) {
  return (
    <div className="space-y-2">
      {medications.map((med) => (
        <div
          key={med.id}
          className="flex items-start justify-between py-3 px-4 bg-bg-surface-tint rounded-lg border border-border-subtle hover:border-border-default transition-colors"
        >
          <div className="flex items-start gap-3">
            <span className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Pill className="w-4 h-4 text-primary-600" />
            </span>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[14px] font-semibold text-text-default">{med.name}</span>
                <Badge variant="outline" className={STATUS_STYLES[med.status] || STATUS_STYLES.active}>
                  {med.status}
                </Badge>
              </div>
              <p className="text-[13px] text-text-muted">
                {med.dosage} — {med.frequency} — {med.route}
              </p>
              <p className="text-[12px] text-text-subtle mt-0.5">
                {med.indication} · Started {med.startDate}
              </p>
              {med.safetyConcern && (
                <div className="flex items-center gap-1.5 mt-1.5 text-[12px] text-warning-600">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {med.safetyConcern}
                </div>
              )}
            </div>
          </div>
          {med.citationId && (
            <button
              onClick={() => onCitationClick && onCitationClick(med.citationId!)}
              className="text-[11px] font-semibold text-primary-600 bg-primary-50 px-1.5 py-0.5 rounded hover:bg-primary-100 transition-colors flex-shrink-0"
            >
              [{med.citationId}]
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
