import { AlertTriangle } from "lucide-react";
import { Link } from "@tanstack/react-router";

export function DegradedBanner({
  message = "HMS API is degraded — patient data may be up to 18 minutes stale.",
  href = "/integrations/hms",
}: {
  message?: string;
  href?: string;
}) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3 rounded-lg border border-warning/40 bg-warning/10 px-4 py-2.5 text-sm text-warning">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" />
        <span className="font-medium text-foreground">{message}</span>
      </div>
      <Link to={href} className="text-xs font-semibold underline-offset-4 hover:underline">
        View sync status →
      </Link>
    </div>
  );
}