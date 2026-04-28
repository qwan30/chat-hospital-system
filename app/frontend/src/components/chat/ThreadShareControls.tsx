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
  onSelectFirstThread,
}: {
  activeThread: ConversationThread | undefined;
  onSelectFirstThread: () => void;
}) {
  const activeLabel = activeThread ? shareStateLabels[activeThread.sharedState] : "Local only";

  return (
    <div className="space-y-3 border-t border-white/10 p-3">
      <div className="grid grid-cols-4 gap-2">
        <Button size="sm" variant="secondary" aria-label="New local sample conversation" onClick={onSelectFirstThread}>
          <MessageSquarePlus className="size-4" />
        </Button>
        <Button size="sm" variant="secondary" aria-label="Rename local sample conversation">
          <Pencil className="size-4" />
        </Button>
        <Button size="sm" variant="secondary" aria-label="Share local sample conversation">
          <Share2 className="size-4" />
        </Button>
        <Button size="sm" variant="secondary" aria-label="Delete local sample conversation">
          <Trash2 className="size-4" />
        </Button>
      </div>
      <Badge className="w-full justify-center border-[#fbbf24]/30 text-[#fbbf24]">
        {activeLabel}: not persisted in Phase 1
      </Badge>
    </div>
  );
}
