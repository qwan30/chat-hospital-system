import { WifiOff } from "lucide-react";
import { useOnlineStatus } from "@/hooks/use-online-status";

export function OfflineBanner() {
  const online = useOnlineStatus();
  if (online) return null;
  return (
    <div
      role="status"
      className="flex items-center gap-2 border-b border-warning/30 bg-warning/10 px-4 py-1.5 text-xs text-warning"
    >
      <WifiOff className="h-3.5 w-3.5" />
      <span className="font-medium">You're offline.</span>
      <span className="opacity-80">Drafts are saved locally and will sync when you're back online.</span>
    </div>
  );
}