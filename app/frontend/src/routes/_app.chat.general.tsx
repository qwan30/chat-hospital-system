import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { ChatMessage } from "@/components/hms/ChatMessage";
import { ChatComposer } from "@/components/hms/ChatComposer";
import { StreamingAssistantMessage } from "@/components/hms/StreamingAssistantMessage";
import type { ChatMessageData } from "@/components/hms/ChatMessage";
import { useState } from "react";

export const Route = createFileRoute("/_app/chat/general")({
  head: () => ({ meta: [{ title: "General chat — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const [messages, setMessages] = useState<ChatMessageData[]>([
    { id: "g1", role: "user", content: "What is the recommended duration of DAPT after DES placement in stable CAD?" },
    {
      id: "g2",
      role: "assistant",
      content:
        "Per the 2023 ACC/AHA guideline, 6 months of DAPT after DES placement in stable CAD is recommended for most patients, with consideration for shorter (1–3 mo) duration if bleeding risk is high. Always individualize based on ischemic vs bleeding risk and shared decision making.",
    },
  ]);
  const [streamingId, setStreamingId] = useState<string | null>("g2");

  const send = (text: string) => {
    const seed = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const replyId = `a-${seed}`;
    setMessages((m) => [
      ...m,
      { id: `u-${seed}`, role: "user", content: text },
      {
        id: replyId,
        role: "assistant",
        content:
          "Drawing on indexed formulary entries and society guidelines, here's a concise answer with the key caveats and the typical monitoring cadence your team should plan for. Please confirm against the latest local protocol before acting.",
      },
    ]);
    setStreamingId(replyId);
  };

  return (
    <AppShell>
      <PageHeader title="General clinical chat" description="No patient context. Cite from formularies and guidelines only." />
      <Card className="flex flex-col">
        <div className="flex-1 space-y-4 p-5">
          {messages.map((m) =>
            m.id === streamingId ? (
              <StreamingAssistantMessage key={m.id} message={m} onComplete={() => setStreamingId(null)} />
            ) : (
              <ChatMessage key={m.id} msg={m} />
            ),
          )}
        </div>
        <div className="border-t p-3">
          <ChatComposer
            onSend={send}
            disabled={streamingId !== null}
            disabledHint="Waiting for current response… stop or resume it above."
          />
        </div>
      </Card>
    </AppShell>
  );
}
