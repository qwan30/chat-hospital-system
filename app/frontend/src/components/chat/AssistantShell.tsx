import { Badge } from "@/components/ui/badge";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { ChatTranscript } from "@/components/chat/ChatTranscript";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EvidencePanel } from "@/components/chat/EvidencePanel";

export function AssistantShell() {
  return (
    <main className="min-h-dvh bg-[#08090a] text-[#f7f8f8]">
      <div className="grid min-h-dvh grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_360px]">
        <ConversationSidebar />

        <section className="order-1 flex min-h-[76dvh] min-w-0 flex-col bg-[#0f1011] lg:order-2 lg:min-h-dvh">
          <header className="flex min-h-16 flex-col justify-center gap-3 border-b border-white/10 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-5">
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase text-[#8a8f98]">Kotaemon-style assistant</p>
              <h1 className="text-lg font-semibold text-white">Ask hospital questions with cited evidence</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge>General scope ready</Badge>
              <Badge className="border-[#34d399]/30 text-[#34d399]">Patient gate visible</Badge>
            </div>
          </header>

          <ChatTranscript />
          <ChatComposer />
        </section>

        <EvidencePanel />
      </div>
    </main>
  );
}
