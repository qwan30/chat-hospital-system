import { Card, CardContent } from "@/components/ui/card";
import { Shield, ChevronRight } from "lucide-react";

interface SafeRefusalCardProps {
  reason: string;
  suggestions?: string[];
}

export function SafeRefusalCard({ reason, suggestions }: SafeRefusalCardProps) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0 mt-1">
        <Shield className="w-4 h-4 text-purple-600" />
      </div>
      <div className="flex-1 max-w-[75%]">
        <Card className="border-purple-100 bg-purple-50/50">
          <CardContent className="p-4 space-y-3">
            <div>
              <h4 className="text-[14px] font-semibold text-purple-700 mb-1">Cannot answer this question</h4>
              <p className="text-[13px] text-text-muted leading-relaxed">{reason}</p>
            </div>
            {suggestions && suggestions.length > 0 && (
              <div>
                <p className="text-[12px] font-medium text-text-default mb-2">What you can do instead:</p>
                <div className="space-y-1.5">
                  {suggestions.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 text-[13px] text-text-muted">
                      <ChevronRight className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                      {s}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
