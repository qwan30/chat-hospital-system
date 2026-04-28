import {
  ChevronDown,
  MessageSquarePlus,
  Moon,
  PanelLeft,
  Pencil,
  Share2,
  Trash2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const conversationThreads = [
  {
    id: "thread-local-policy",
    title: "Ward transfer policy",
    detail: "General knowledge",
    active: true,
    marker: "Local sample",
  },
  {
    id: "thread-local-patient",
    title: "Patient context review",
    detail: "Permission gated",
    active: false,
    marker: "Not persisted",
  },
  {
    id: "thread-local-evidence",
    title: "Citation walkthrough",
    detail: "Evidence preview",
    active: false,
    marker: "Local sample",
  },
];

export function ConversationSidebar() {
  return (
    <aside className="order-2 flex min-h-[320px] min-w-0 flex-col border-t border-white/10 bg-[#0b0c0d] lg:order-1 lg:min-h-dvh lg:border-r lg:border-t-0">
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase text-[#8a8f98]">Conversations</p>
          <h2 className="truncate text-base font-semibold text-white">Hospital Assistant</h2>
        </div>
        <div className="flex items-center gap-1">
          <Button size="icon" variant="ghost" aria-label="Toggle dark mode">
            <Moon className="size-4" />
          </Button>
          <Button size="icon" variant="ghost" aria-label="Collapse conversation panel">
            <PanelLeft className="size-4" />
          </Button>
        </div>
      </div>

      <div className="border-b border-white/10 p-3">
        <Button className="w-full justify-between" type="button">
          <span className="inline-flex items-center gap-2">
            <MessageSquarePlus className="size-4" />
            New conversation
          </span>
          <ChevronDown className="size-4 opacity-70" />
        </Button>
      </div>

      <nav className="flex-1 space-y-2 overflow-y-auto p-3" aria-label="Conversation threads">
        {conversationThreads.map((thread) => (
          <button
            key={thread.id}
            className={
              "w-full rounded-md border px-3 py-3 text-left transition-colors " +
              (thread.active
                ? "border-[#5e6ad2]/50 bg-[#5e6ad2]/15 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
                : "border-transparent bg-white/[0.03] text-[#d0d6e0] hover:bg-white/[0.06]")
            }
            type="button"
            aria-current={thread.active ? "page" : undefined}
          >
            <span className="block truncate text-sm font-medium">{thread.title}</span>
            <span className="mt-1 flex items-center justify-between gap-2 text-xs text-[#8a8f98]">
              <span className="truncate">{thread.detail}</span>
              <span>{thread.marker}</span>
            </span>
          </button>
        ))}
      </nav>

      <div className="space-y-3 border-t border-white/10 p-3">
        <div className="grid grid-cols-3 gap-2">
          <Button size="sm" variant="secondary" aria-label="Rename conversation">
            <Pencil className="size-4" />
          </Button>
          <Button size="sm" variant="secondary" aria-label="Share conversation">
            <Share2 className="size-4" />
          </Button>
          <Button size="sm" variant="secondary" aria-label="Delete conversation">
            <Trash2 className="size-4" />
          </Button>
        </div>
        <Badge className="w-full justify-center border-[#fbbf24]/30 text-[#fbbf24]">
          Shared threads are local/sample in Phase 1
        </Badge>
      </div>
    </aside>
  );
}
