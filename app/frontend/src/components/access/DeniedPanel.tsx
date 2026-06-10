import { Card, CardContent } from "@/components/ui/card";
import { Shield, Clock, AlertTriangle } from "lucide-react";

interface DeniedPanelProps {
  patientName: string;
  reason: string;
}

export function DeniedPanel({ patientName, reason }: DeniedPanelProps) {
  return (
    <Card className="border-danger-100">
      <CardContent className="py-8 text-center">
        <div className="w-14 h-14 rounded-xl bg-danger-50 flex items-center justify-center mx-auto mb-4"><Shield className="w-7 h-7 text-danger-500" /></div>
        <h2 className="text-h3 text-text-strong mb-2">Access Denied</h2>
        <p className="text-body text-text-muted mb-1">You cannot view {patientName}&apos;s record.</p>
        <p className="text-[12px] text-text-subtle">{reason}</p>
      </CardContent>
    </Card>
  );
}
