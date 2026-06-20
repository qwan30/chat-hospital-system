import { useSession } from "@/lib/session";
import { ROLE_LABEL, ROLE_TONE } from "@/lib/rbac";
import { useState } from "react";
import { X, UserCog } from "lucide-react";
import { cn } from "@/lib/utils";

export function ActingAsBanner() {
  const { session } = useSession();
  const [dismissed, setDismissed] = useState(false);
  if (!session || session.isRealAuth || dismissed) return null;
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 border-b px-4 py-1.5 text-xs",
        ROLE_TONE[session.role],
      )}
    >
      <div className="flex items-center gap-2">
        <UserCog className="h-3.5 w-3.5" />
        <span className="font-medium">
          Demo mode: You are signed in as {ROLE_LABEL[session.role]} in {session.workspace.name}.
        </span>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="rounded p-0.5 hover:bg-foreground/10"
        aria-label="Dismiss banner"
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}
