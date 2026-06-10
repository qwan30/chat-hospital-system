import { Shield, Clock, User, Bell, Lock } from "lucide-react";

export function ExplainerTimeline() {
  return (
    <div className="space-y-3">
      {[
        { icon: Shield, label: "Request submitted", desc: "Your justification is recorded" },
        { icon: Clock, label: "Review", desc: "Approved within SLA timeframe" },
        { icon: User, label: "Access granted", desc: "Time-limited access activated" },
        { icon: Bell, label: "Notification", desc: "Attending physician alerted" },
        { icon: Lock, label: "Auto-revoke", desc: "Access expires after duration" },
      ].map((s, i) => (
        <div key={i} className="flex items-start gap-3">
          <span className="w-7 h-7 rounded-full bg-bg-surface-tint border border-border-subtle flex items-center justify-center flex-shrink-0"><s.icon className="w-3.5 h-3.5 text-text-subtle" /></span>
          <div><p className="text-[13px] font-medium text-text-default">{s.label}</p><p className="text-[11px] text-text-muted">{s.desc}</p></div>
        </div>
      ))}
    </div>
  );
}
