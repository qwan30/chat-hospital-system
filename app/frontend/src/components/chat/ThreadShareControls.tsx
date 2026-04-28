import { MessageSquarePlus, Pencil, Share2, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ConversationThread } from "@/lib/chat-assistant";

const shareStateLabels: Record<ConversationThread["sharedState"], string> = {
  "local-only": "Local only",
  "sample-shared": "Sample shared",
  "backend-persisted": "Backend persisted",
};

export function ThreadShareControls({
  activeThread,
  onArchiveThread,
  onCreateThread,
  onRenameThread,
  onShareThread,
}: {
  activeThread: ConversationThread | undefined;
  onArchiveThread: () => void;
  onCreateThread: () => void;
  onRenameThread: () => void;
  onShareThread: () => void;
}) {
  const activeLabel = activeThread ? shareStateLabels[activeThread.sharedState] : "Local only";
  const participantLabel = activeThread
    ? `${activeThread.participants.length} participant${activeThread.participants.length === 1 ? "" : "s"}`
    : "No active thread";

  return (
    <div className="space-y-3 border-t border-white/10 p-3">
      <div className="grid grid-cols-4 gap-2">
        <Button size="sm" variant="secondary" aria-label="Create backend conversation" onClick={onCreateThread}>
          <MessageSquarePlus className="size-4" />
        </Button>
        <Button size="sm" variant="secondary" aria-label="Rename backend conversation" disabled={!activeThread} onClick={onRenameThread}>
          <Pencil className="size-4" />
        </Button>
        <Button size="sm" variant="secondary" aria-label="Share backend conversation" disabled={!activeThread} onClick={onShareThread}>
          <Share2 className="size-4" />
        </Button>
        <Button size="sm" variant="secondary" aria-label="Archive backend conversation" disabled={!activeThread} onClick={onArchiveThread}>
          <Trash2 className="size-4" />
        </Button>
      </div>
      <Badge className="w-full justify-center border-[#fbbf24]/30 text-[#fbbf24]">
        {activeLabel}: {participantLabel}
      </Badge>
    </div>
  );
}
