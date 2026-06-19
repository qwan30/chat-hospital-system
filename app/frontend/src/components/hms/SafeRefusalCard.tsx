import { Card } from "@/components/ui/card";
import { ShieldQuestion } from "lucide-react";

export function SafeRefusalCard({ reason }: { reason?: string }) {
  return (
    <Card className="border-warning/30 bg-warning/5 p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-warning/15 text-warning">
          <ShieldQuestion className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold">Insufficient evidence to answer</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {reason ??
              "I couldn't find authoritative sources in the indexed knowledge base. Please verify with a clinician or upload supporting documents."}
          </p>
        </div>
      </div>
    </Card>
  );
}
