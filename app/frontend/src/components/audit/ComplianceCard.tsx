import { Card, CardContent } from "@/components/ui/card";
import { ShieldCheck } from "lucide-react";

interface ComplianceCardProps {
  complianceRate?: number;
  daysWithoutViolation?: number;
}

export function ComplianceCard({ complianceRate = 100, daysWithoutViolation = 30 }: ComplianceCardProps) {
  return (
    <Card className="border-success-100 bg-success-50/50">
      <CardContent className="p-4 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-[14px] font-semibold text-success-700">{complianceRate}% Compliance</p>
          <p className="text-[12px] text-success-600">All sensitive queries are logged and monitored. No policy violations detected in the last {daysWithoutViolation} days.</p>
        </div>
      </CardContent>
    </Card>
  );
}
