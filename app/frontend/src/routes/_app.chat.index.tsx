import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { Card } from "@/components/ui/card";
import { ChatComposer } from "@/components/hms/ChatComposer";
import { Logo } from "@/components/hms/Logo";
import { threads } from "@/data/threads";
import { Clock, MessageSquare, Sparkles } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/_app/chat/")({
  head: () => ({
    meta: [
      { title: "Chat — HMS AI Copilot" },
      { name: "description", content: "Ask the hospital knowledge assistant." },
    ],
  }),
  component: ChatLanding,
});

const suggestions = [
  "Summarize the latest ACC/AHA atrial fibrillation guideline",
  "What is our hospital's sepsis 1-hour bundle?",
  "DOAC renal-dose adjustment rules for apixaban",
  "Differential for new-onset dyspnea in a 70-year-old with HFrEF",
];

function ChatLanding() {
  const navigate = useNavigate();
  const [composerText, setComposerText] = useState("");
  return (
    <AppShell
      rightRail={
        <Card className="p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
            <Clock className="h-4 w-4 text-muted-foreground" /> Recent threads
          </div>
          <ul className="space-y-1">
            {threads.map((t) => (
              <li key={t.id}>
                <Link
                  to={t.patientId ? "/chat/patients/$patientId" : "/chat"}
                  params={t.patientId ? { patientId: t.patientId } : undefined}
                  className="block rounded-md p-2 hover:bg-muted"
                >
                  <div className="flex items-start gap-2">
                    <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ai" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{t.title}</p>
                      <p className="text-xs text-muted-foreground">{t.updated}</p>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      }
    >
      <div className="mx-auto flex max-w-3xl flex-col items-center pt-10 text-center">
        <Logo size={56} />
        <h1 className="mt-5 text-3xl font-semibold tracking-tight">How can I help you today?</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Cited answers from your hospital's indexed knowledge base. PHI-safe and audit-logged.
        </p>
        <div className="mt-6 grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => setComposerText(s)}
              className="rounded-xl border bg-card p-3 text-left text-sm hover:bg-accent cursor-pointer"
            >
              <Sparkles className="mb-2 h-4 w-4 text-ai" />
              {s}
            </button>
          ))}
        </div>
        <div className="mt-6 w-full">
          <ChatComposer
            value={composerText}
            onValueChange={setComposerText}
            onSend={() => {
              navigate({ to: "/chat/patients/$patientId", params: { patientId: "p-001" } });
            }}
          />
        </div>
      </div>
    </AppShell>
  );
}
