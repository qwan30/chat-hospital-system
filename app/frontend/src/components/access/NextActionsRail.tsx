import { Card, CardContent } from "@/components/ui/card";
import { Lock, Clock, Bell } from "lucide-react";

export function NextActionsRail() {
  return (
    <Card><CardContent className="p-4 space-y-3">
      <h4 className="text-h4 text-text-strong">Next Steps</h4>
      <div className="space-y-2">{[{ icon: Lock, text: "Submit emergency access request" }, { icon: Clock, text: "Wait for care team assignment" }, { icon: Bell, text: "Contact attending physician" }].map((item, i) => <div key={i} className="flex items-start gap-2"><item.icon className="w-4 h-4 text-text-subtle mt-0.5" /><p className="text-[13px] text-text-default">{item.text}</p></div>)}</div>
    </CardContent></Card>
  );
}
