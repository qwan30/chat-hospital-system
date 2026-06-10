import { CheckCircle, Shield, Lock, Eye } from "lucide-react";

const CHECKS = [
  { icon: Shield, label: "Source integrity", passed: true },
  { icon: Lock, label: "Permission verified", passed: true },
  { icon: Eye, label: "Sensitivity review", passed: true },
];

export function VerificationChecklist() {
  return (
    <div className="space-y-2">
      {CHECKS.map((check, i) => (
        <div key={i} className="flex items-center gap-2 text-[12px]">
          <CheckCircle className="w-3.5 h-3.5 text-success-500 flex-shrink-0" />
          <check.icon className="w-3.5 h-3.5 text-text-subtle flex-shrink-0" />
          <span className="text-text-muted">{check.label}</span>
          <span className="ml-auto text-success-600 text-[10px] font-medium">Passed</span>
        </div>
      ))}
    </div>
  );
}
