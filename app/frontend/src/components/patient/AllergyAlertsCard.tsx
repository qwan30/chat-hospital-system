import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, ShieldCheck } from "lucide-react";

interface Allergy {
  id: string;
  allergen: string;
  severity: "high" | "medium" | "low";
  reaction: string;
  recordedDate: string;
}

interface AllergyAlertsCardProps {
  allergies: Allergy[];
}

const SEVERITY_STYLES: Record<string, string> = {
  high: "bg-danger-50 text-danger-600 border-danger-100",
  medium: "bg-warning-50 text-warning-500 border-warning-100",
  low: "bg-bg-surface-tint text-text-muted border-border-subtle",
};

const SEVERITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  high: AlertTriangle,
  medium: AlertTriangle,
  low: ShieldCheck,
};

export function AllergyAlertsCard({ allergies }: AllergyAlertsCardProps) {
  return (
    <Card className="border-warning-100">
      <CardHeader className="pb-2">
        <CardTitle className="text-h4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-warning-500" />
          Allergy Alerts
        </CardTitle>
      </CardHeader>
      <CardContent>
        {allergies.length === 0 ? (
          <p className="text-[13px] text-text-muted py-2">No known allergies recorded.</p>
        ) : (
          <div className="space-y-2">
            {allergies.map((a) => {
              const Icon = SEVERITY_ICONS[a.severity];
              const style = SEVERITY_STYLES[a.severity];
              return (
                <div key={a.id} className={"flex items-start gap-3 p-3 rounded-lg border " + style}>
                  <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[13px] font-semibold">{a.allergen}</span>
                    <p className="text-[12px] mt-0.5">
                      {a.reaction} · Recorded {a.recordedDate}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
