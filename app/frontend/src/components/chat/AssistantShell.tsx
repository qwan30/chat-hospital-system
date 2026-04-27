import { Bot, FileText, LockKeyhole, MessageSquarePlus, PanelRightOpen, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const conversationThreads = [
  {
    id: "thread-local-policy",
    title: "Ward transfer policy",
    detail: "General scope",
    active: true,
  },
  {
    id: "thread-local-patient",
    title: "Patient context review",
    detail: "Local sample only",
    active: false,
  },
];

export function AssistantShell() {
  return (
    <main className="min-h-screen bg-[#08090a] text-[#f7f8f8]">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_340px]">
        <aside className="flex min-h-[280px] flex-col border-b border-white/10 bg-[#0b0c0d] lg:min-h-screen lg:border-b-0 lg:border-r">
          <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
            <div>
              <p className="text-xs font-medium uppercase text-[#8a8f98]">Hospital Assistant</p>
              <h1 className="text-base font-semibold">Chat Workspace</h1>
            </div>
            <Button size="icon" aria-label="New conversation">
              <MessageSquarePlus className="size-4" />
            </Button>
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto p-3">
            {conversationThreads.map((thread) => (
              <button
                key={thread.id}
                className={
                  "w-full rounded-md border px-3 py-3 text-left transition-colors " +
                  (thread.active
                    ? "border-[#5e6ad2]/50 bg-[#5e6ad2]/15 text-white"
                    : "border-transparent bg-white/[0.03] text-[#d0d6e0] hover:bg-white/[0.06]")
                }
                type="button"
              >
                <span className="block text-sm font-medium">{thread.title}</span>
                <span className="mt-1 block text-xs text-[#8a8f98]">{thread.detail}</span>
              </button>
            ))}
          </div>

          <div className="border-t border-white/10 p-3">
            <Badge className="w-full justify-center border-[#fbbf24]/30 text-[#fbbf24]">
              Shared threads are local/sample
            </Badge>
          </div>
        </aside>

        <section className="flex min-h-[620px] flex-col bg-[#0f1011]">
          <header className="flex min-h-16 flex-col justify-center gap-2 border-b border-white/10 px-5 py-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-medium uppercase text-[#8a8f98]">Kotaemon-style assistant</p>
              <h2 className="text-lg font-semibold">Ask hospital questions with cited evidence</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge>General scope</Badge>
              <Badge className="border-[#34d399]/30 text-[#34d399]">Permission gate visible</Badge>
            </div>
          </header>

          <div className="flex-1 space-y-5 overflow-y-auto px-5 py-6">
            <div className="max-w-3xl rounded-md border border-white/10 bg-white/[0.03] p-4">
              <div className="mb-3 flex items-center gap-2 text-sm text-[#a3a7ad]">
                <Bot className="size-4 text-[#5e6ad2]" />
                Assistant answer surface
              </div>
              <p className="text-sm leading-6 text-[#e2e4e7]">
                Open into chat first. Answers, citations, patient gates, and evidence review mount here as the next
                Phase 1 beads add typed data and states.
              </p>
            </div>

            <div className="ml-auto max-w-2xl rounded-md border border-[#5e6ad2]/30 bg-[#5e6ad2]/10 p-4">
              <p className="text-sm leading-6 text-[#eef0ff]">
                What is the ward transfer policy for a patient-linked question?
              </p>
            </div>
          </div>

          <form className="border-t border-white/10 p-4">
            <label className="sr-only" htmlFor="assistant-question">
              Ask the hospital assistant
            </label>
            <div className="flex min-h-12 items-center gap-3 rounded-md border border-white/10 bg-[#08090a] px-3">
              <Search className="size-4 shrink-0 text-[#8a8f98]" />
              <input
                className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-[#6f747d]"
                id="assistant-question"
                placeholder="Ask general hospital knowledge, or select a patient context first..."
                type="text"
              />
              <Button size="sm" type="button">
                Ask
              </Button>
            </div>
          </form>
        </section>

        <aside className="min-h-[320px] border-t border-white/10 bg-[#111214] lg:min-h-screen lg:border-l lg:border-t-0">
          <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
            <div>
              <p className="text-xs font-medium uppercase text-[#8a8f98]">Evidence</p>
              <h2 className="text-base font-semibold">Source Panel</h2>
            </div>
            <Button size="icon" variant="ghost" aria-label="Toggle evidence panel">
              <PanelRightOpen className="size-4" />
            </Button>
          </div>

          <div className="space-y-3 p-4">
            <div className="rounded-md border border-white/10 bg-white/[0.03] p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                <FileText className="size-4 text-[#60a5fa]" />
                Citation region
              </div>
              <p className="text-sm leading-5 text-[#a3a7ad]">
                Cited documents, pages, chunks, and unavailable states will render here after evidence-state beads.
              </p>
            </div>

            <div className="rounded-md border border-[#f87171]/30 bg-[#f87171]/10 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-[#fecaca]">
                <LockKeyhole className="size-4" />
                Patient data is gated
              </div>
              <p className="text-sm leading-5 text-[#f5b4b4]">
                Patient-linked citations stay hidden until backend permission validation allows access.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
