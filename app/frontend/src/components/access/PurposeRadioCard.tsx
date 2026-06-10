import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface PurposeRadioCardProps { value: string; onChange: (v: string) => void; }

const PURPOSES = [
  { value: "immediate_care", label: "Immediate Patient Care", desc: "Direct clinical decision-making for this patient" },
  { value: "care_coordination", label: "Care Coordination", desc: "Coordinating care across multiple providers" },
  { value: "records_review", label: "Records Review", desc: "Reviewing historical records for context" },
];

export function PurposeRadioCard({ value, onChange }: PurposeRadioCardProps) {
  return (
    <RadioGroup value={value} onValueChange={onChange} className="space-y-2">
      {PURPOSES.map((p) => (
        <Label key={p.value} className={"flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors " + (value === p.value ? "border-primary-500 bg-primary-50" : "border-border-subtle hover:border-border-default")}>
          <RadioGroupItem value={p.value} className="mt-0.5" />
          <div><p className="text-[13px] font-medium text-text-default">{p.label}</p><p className="text-[12px] text-text-muted">{p.desc}</p></div>
        </Label>
      ))}
    </RadioGroup>
  );
}
