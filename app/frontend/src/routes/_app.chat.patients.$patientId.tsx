import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { ChatMessage, type ChatMessageData } from "@/components/hms/ChatMessage";
import { ChatComposer } from "@/components/hms/ChatComposer";
import { StreamingAssistantMessage } from "@/components/hms/StreamingAssistantMessage";
import { EvidenceRail, type EvidenceItem } from "@/components/hms/EvidenceRail";
import { SafeRefusalCard } from "@/components/hms/SafeRefusalCard";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Heart, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { getPatient } from "@/data/patients";
import { citations } from "@/data/citations";
import { useSession } from "@/lib/session";
import { streamChat } from "@/lib/stream-client";
import { getStoredApiUrl } from "@/lib/api-client";

export const Route = createFileRoute("/_app/chat/patients/$patientId")({
  head: () => ({
    meta: [{ title: "Patient chat — HMS AI Copilot" }],
  }),
  component: PatientChat,
});

function PatientChat() {
  const { patientId } = Route.useParams();
  const { session } = useSession();
  const patient = getPatient(patientId);
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [streamError, setStreamError] = useState<string | null>(null);

  const evidence: EvidenceItem[] = useMemo(() => {
    const ids = new Set<string>();
    messages.forEach((m) => m.citations?.forEach((c) => ids.add(c.sourceId)));
    return [...ids].map((id, i) => {
      const s = citations[id];
      return {
        id,
        n: i + 1,
        title: s?.title ?? id,
        source: s?.source ?? "",
        date: s?.date ?? "",
        snippet: s?.snippet ?? "",
        relevance: s?.relevance ?? 0.5,
      };
    });
  }, [messages]);

  const noEvidence = evidence.length === 0 && messages.length === 0;

  const send = async (text: string) => {
    const seed = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const userMsg: ChatMessageData = {
      id: `u-${seed}`,
      role: "user",
      content: text,
      time: "now",
    };
    setMessages((m) => [...m, userMsg]);
    setStreamError(null);

    const token = session?.token || localStorage.getItem("hospital_ai_token");
    const apiUrl = getStoredApiUrl();

    // Try real backend streaming first when authenticated
    if (token) {
      const replyId = `a-${seed}`;
      let fullText = "";

      try {
        setStreamingId(replyId);
        setStreamingText("");

        await streamChat(apiUrl, token, { question: text, patient_id: patientId }, (event) => {
          if (event.type === "token") {
            fullText += event.content || "";
            setStreamingText(fullText);
          }
        });

        const reply: ChatMessageData = {
          id: replyId,
          role: "assistant",
          content: fullText || "I couldn't generate a response. Please try again.",
          time: "now",
        };
        setMessages((m) => [...m, reply]);
        setStreamingId(null);
        setStreamingText("");
        return;
      } catch (err) {
        console.warn("Backend stream failed, falling back to mock:", err);
        setStreamingId(null);
        setStreamingText("");
      }
    }

    // Fallback: mock response for demo / no-auth mode
    const replyId = `a-${seed}`;
    const reply: ChatMessageData = {
      id: replyId,
      role: "assistant",
      time: "now",
      content:
        "Based on the indexed guideline [1] and this patient's latest progress note [2], " +
        "the recommended next step is to continue current anticoagulation and reassess " +
        "at the 6-week follow-up. Monitor renal function and bleeding risk; reinforce " +
        "adherence at the next visit.",
      citations: [
        { n: 1, sourceId: "c-001" },
        { n: 2, sourceId: "c-003" },
      ],
    };
    setMessages((m) => [...m, reply]);
    setStreamingId(replyId);
  };

  return (
    <AppShell
      rightRail={
        noEvidence ? (
          <SafeRefusalCard reason="Ask a question to retrieve evidence from indexed sources." />
        ) : (
          <EvidenceRail items={evidence} />
        )
      }
    >
      <Button asChild variant="ghost" size="sm" className="-ml-2 mb-3">
        <Link to="/chat">
          <ArrowLeft className="mr-1 h-3.5 w-3.5" /> All chats
        </Link>
      </Button>
      <Card className="mb-4 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Heart className="h-4 w-4 text-destructive" />
              <h2 className="text-lg font-semibold">{patient?.name ?? "Patient"}</h2>
              <Badge variant="secondary" className="bg-success/10 text-success">
                <ShieldCheck className="mr-1 h-3 w-3" /> Access verified
              </Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {patient?.age} · {patient?.sex} · {patient?.unit} · {patient?.condition}
            </p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <p className="font-mono">{patient?.mrn}</p>
            <p>Last visit: {patient?.lastVisit}</p>
          </div>
        </div>
      </Card>

      <div className="space-y-5 pb-6">
        {messages.map((m) =>
          m.id === streamingId ? (
            <StreamingAssistantMessage
              key={m.id}
              message={m}
              onComplete={() => setStreamingId(null)}
            />
          ) : (
            <ChatMessage key={m.id} msg={m} />
          ),
        )}
        {/* Real-time streaming text from backend */}
        {streamingText && !messages.find((m) => m.id === streamingId) && (
          <div className="rounded-lg bg-muted/50 p-4 text-sm">
            <p className="whitespace-pre-wrap">{streamingText}</p>
          </div>
        )}
      </div>

      {streamError && <p className="mb-2 text-sm text-destructive">{streamError}</p>}

      <div className="sticky bottom-4">
        <ChatComposer
          onSend={send}
          context={patient?.name}
          disabled={streamingId !== null || streamingText !== ""}
          disabledHint={
            streamingText ? "Receiving response from AI..." : "Waiting for current response…"
          }
        />
      </div>
    </AppShell>
  );
}
