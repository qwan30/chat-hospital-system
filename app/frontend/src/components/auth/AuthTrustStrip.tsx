import { Shield } from "lucide-react";

export function AuthTrustStrip() {
  return (
    <div className="flex justify-center gap-4 pt-2">
      {["PHI Protection", "Audit Logging", "Role-Based Access"].map((t) => (
        <span key={t} className="text-[11px] text-text-muted flex items-center gap-1">
          <Shield className="w-3 h-3 text-success-600" /> {t}
        </span>
      ))}
    </div>
  );
}
