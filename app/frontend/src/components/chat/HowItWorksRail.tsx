import { Card, CardContent } from "@/components/ui/card";
import { Search, FileText, Brain, Shield } from "lucide-react";

const STEPS = [
  { icon: Search, title: "1. Query", description: "Your question is analyzed for clinical intent and relevant context" },
  { icon: FileText, title: "2. Retrieve", description: "The system searches indexed patient documents and guidelines" },
  { icon: Brain, title: "3. Generate", description: "AI synthesizes an evidence-backed response with citations" },
  { icon: Shield, title: "4. Verify", description: "Safety checks validate clinical appropriateness before delivery" },
];

export function HowItWorksRail() {
  return (
    <Card>
      <CardContent className="p-4">
        <h4 className="text-h4 text-text-strong mb-3">How it works</h4>
        <div className="space-y-3">
          {STEPS.map((step, i) => (
            <div key={i} className="flex items-start gap-3">
              <span className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                <step.icon className="w-4 h-4 text-primary-600" />
              </span>
              <div>
                <p className="text-[13px] font-medium text-text-default">{step.title}</p>
                <p className="text-[11px] text-text-muted leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
