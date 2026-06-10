import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface JustificationTextareaProps { value: string; onChange: (v: string) => void; }

export function JustificationTextarea({ value, onChange }: JustificationTextareaProps) {
  return (
    <div className="space-y-1.5">
      <Label className="text-[12px]">Clinical Justification</Label>
      <Textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder="Describe why access is clinically necessary for this patient..." className="min-h-[80px]" maxLength={500} />
      <p className="text-[11px] text-text-subtle text-right">{value.length}/500 characters</p>
    </div>
  );
}
