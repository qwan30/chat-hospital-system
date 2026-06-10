import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Info } from "lucide-react";

interface GeneralKnowledgeToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export function GeneralKnowledgeToggle({ enabled, onToggle }: GeneralKnowledgeToggleProps) {
  return (
    <div className="flex items-center justify-between p-3 bg-bg-surface-tint rounded-lg border border-border-subtle">
      <div className="flex items-center gap-2">
        <Info className="w-4 h-4 text-text-subtle" />
        <div>
          <Label className="text-[13px] font-medium text-text-default">General Medical Knowledge</Label>
          <p className="text-[11px] text-text-subtle">Use broad knowledge when patient-specific data is unavailable</p>
        </div>
      </div>
      <Switch checked={enabled} onCheckedChange={onToggle} />
    </div>
  );
}
