import { Loader2, Search, CheckCircle, FileText } from "lucide-react";

const STEPS = [
  { icon: Search, label: "Retrieving", description: "Searching indexed documents" },
  { icon: FileText, label: "Validating", description: "Checking source integrity" },
  { icon: CheckCircle, label: "Streaming", description: "Delivering evidence" },
];

export function RetrievalStepper({ activeStep = 0 }: { activeStep?: number }) {
  return (
    <div className="space-y-3">
      {STEPS.map((step, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className={"w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 " + (i < activeStep ? "bg-success-50 text-success-600" : i === activeStep ? "bg-primary-50 text-primary-600" : "bg-bg-surface-tint text-text-subtle")}>
            {i < activeStep ? <CheckCircle className="w-3.5 h-3.5" /> : i === activeStep ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <step.icon className="w-3.5 h-3.5" />}
          </span>
          <div>
            <p className={"text-[12px] font-medium " + (i <= activeStep ? "text-text-default" : "text-text-subtle")}>{step.label}</p>
            <p className="text-[11px] text-text-subtle">{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
