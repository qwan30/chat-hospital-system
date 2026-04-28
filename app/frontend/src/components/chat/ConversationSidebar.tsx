"use client";

import { ChevronDown, MessageSquarePlus, Moon, PanelLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ThreadShareControls } from "@/components/chat/ThreadShareControls";
import type { ConversationThread } from "@/lib/chat-assistant";

export function ConversationSidebar({
  activeThread,
  activeThreadId,
  onSelectFirstThread,
  onSelectThread,
  threads,
}: {
  activeThread: ConversationThread | undefined;
  activeThreadId: string;
  onSelectFirstThread: () => void;
  onSelectThread: (threadId: string) => void;
  threads: ConversationThread[];
}) {
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
        <Button className="w-full justify-between" type="button" onClick={onSelectFirstThread}>
          <span className="inline-flex items-center gap-2">
            <MessageSquarePlus className="size-4" />
            New conversation
          </span>
          <ChevronDown className="size-4 opacity-70" />
        </Button>
      </div>

      <nav className="flex-1 space-y-2 overflow-y-auto p-3" aria-label="Conversation threads">
        {threads.map((thread) => (
          <button
            key={thread.id}
            className={
              "w-full rounded-md border px-3 py-3 text-left transition-colors " +
              (thread.id === activeThreadId
                ? "border-[#5e6ad2]/50 bg-[#5e6ad2]/15 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
                : "border-transparent bg-white/[0.03] text-[#d0d6e0] hover:bg-white/[0.06]")
            }
            type="button"
            aria-current={thread.id === activeThreadId ? "page" : undefined}
            onClick={() => onSelectThread(thread.id)}
          >
            <span className="block truncate text-sm font-medium">{thread.title}</span>
            <span className="mt-1 flex items-center justify-between gap-2 text-xs text-[#8a8f98]">
              <span className="truncate">{thread.description}</span>
              <span>{thread.provenance.visibleLabel}</span>
            </span>
          </button>
        ))}
      </nav>

      <ThreadShareControls
        activeThread={activeThread}
        onSelectFirstThread={onSelectFirstThread}
      />
    </aside>
  );
}
