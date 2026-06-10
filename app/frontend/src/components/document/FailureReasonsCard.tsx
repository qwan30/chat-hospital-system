import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, XCircle } from "lucide-react";

export function FailureReasonsCard({ reasons }: { reasons: string[] }) {
  return (
    <Card className="border-danger-100">
      <CardHeader className="pb-2"><CardTitle className="text-h4 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-danger-500" />Processing Issues</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-2">
          {reasons.map((r, i) => <div key={i} className="flex items-center gap-2 text-[13px] text-text-muted"><XCircle className="w-3.5 h-3.5 text-danger-400 flex-shrink-0" />{r}</div>)}
        </div>
      </CardContent>
    </Card>
  );
}
