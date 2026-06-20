import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { z } from "zod";
import { AppShell } from "@/components/shell/AppShell";
import { Card } from "@/components/ui/card";
import { ChatComposer } from "@/components/hms/ChatComposer";
import { Logo } from "@/components/hms/Logo";
import { Clock, MessageSquare, Sparkles, Heart, ShieldCheck } from "lucide-react";
import { useState, useMemo } from "react";
import { ChatMessage, type ChatMessageData } from "@/components/hms/ChatMessage";
import { EvidenceRail, type EvidenceItem } from "@/components/hms/EvidenceRail";
import { SafeRefusalCard } from "@/components/hms/SafeRefusalCard";
import { Badge } from "@/components/ui/badge";
import { searchPatients, getPatient } from "@/lib/api/patients";
import { useSession } from "@/lib/session";
import { streamChat } from "@/lib/stream-client";
import { getStoredApiUrl } from "@/lib/api-client";
import { uploadDocument } from "@/lib/api/documents";
import { useQuery } from "@tanstack/react-query";
import { listChatThreads } from "@/lib/api/chat-threads";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { ChevronDown, X, AlertTriangle, Loader2, Square } from "lucide-react";
import { useRef } from "react";

const chatSearchSchema = z.object({
  patient: z.string().optional(),
  thread: z.string().optional(),
});

export const Route = createFileRoute("/_app/chat/")({
  validateSearch: chatSearchSchema,
  head: () => ({
    meta: [
      { title: "Chat — HMS AI Copilot" },
      { name: "description", content: "Ask the hospital knowledge assistant." },
    ],
  }),
  component: GlobalChat,
});

const suggestions = [
  "Summarize the latest ACC/AHA atrial fibrillation guideline",
  "What is our hospital's sepsis 1-hour bundle?",
  "DOAC renal-dose adjustment rules for apixaban",
  "Differential for new-onset dyspnea in a 70-year-old with HFrEF",
];

function GlobalChat() {
  const { patient: patientId, thread } = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const { session } = useSession();

  const [composerText, setComposerText] = useState("");
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [streamError, setStreamError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const stopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const { data: backendThreads } = useQuery({
    queryKey: ["chat-threads"],
    queryFn: listChatThreads,
    enabled: !!session?.token,
  });

  const { data: currentPatient } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => getPatient(patientId!),
    enabled: !!patientId,
  });

  const { data: searchResponse } = useQuery({
    queryKey: ["patients", ""],
    queryFn: () => searchPatients(undefined, 50),
    enabled: !!session?.token,
  });

  const patientsList = searchResponse?.items || [];

  const contextNode = (
    <div className="flex items-center gap-1">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Badge
            variant="secondary"
            className="cursor-pointer bg-primary/10 text-primary hover:bg-primary/20"
          >
            <Sparkles className="mr-1 h-3 w-3" />
            {currentPatient
              ? `Context: Patient — ${currentPatient.full_name}`
              : "Context: General hospital knowledge"}
            <ChevronDown className="ml-1 h-3 w-3" />
          </Badge>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-[300px] max-h-[300px] overflow-y-auto">
          <DropdownMenuItem
            onClick={() => navigate({ search: (prev) => ({ ...prev, patient: undefined }) })}
          >
            General hospital knowledge
          </DropdownMenuItem>
          {patientsList.map((p) => (
            <DropdownMenuItem
              key={p.id}
              onClick={() => navigate({ search: (prev) => ({ ...prev, patient: p.id }) })}
            >
              <div className="flex flex-col w-full">
                <div className="flex justify-between">
                  <span className="font-medium">{p.full_name}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {p.mrn} - {p.department || "--"}
                </span>
              </div>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      {currentPatient && (
        <Button
          variant="ghost"
          size="icon"
          className="h-5 w-5 rounded-full hover:bg-muted"
          onClick={() => navigate({ search: (prev) => ({ ...prev, patient: undefined }) })}
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </div>
  );

  const evidence: EvidenceItem[] = useMemo(() => {
    const items: EvidenceItem[] = [];
    const ids = new Set<string>();

    let globalIndex = 1;
    messages.forEach((m) => {
      m.rawCitations?.forEach((c) => {
        if (!ids.has(c.evidence_id)) {
          ids.add(c.evidence_id);
          items.push({
            id: c.evidence_id,
            n: globalIndex++, // assign a global numbering for the Evidence Rail
            title: c.document_title || "Unknown Document",
            source: `Page ${c.page || 1}`,
            date: "Recent", // backend doesn't supply date yet
            snippet: c.content || "",
            relevance: c.score ?? 0.5,
            document_id: c.document_id,
          });
        }
      });
    });
    return items;
  }, [messages]);

  const noEvidence = evidence.length === 0 && messages.length === 0;

  const send = async (text: string, file?: File) => {
    const seed = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    setStreamError(null);
    let uploadedDocId: string | undefined;

    if (file) {
      if (!patientId) {
        setStreamError("A patient context is required to upload a document.");
        return;
      }
      try {
        const doc = await uploadDocument(patientId, file.name, "Chat Attachment", file);
        uploadedDocId = doc.id;
      } catch (err) {
        setStreamError("Failed to upload the document. Please try again.");
        return;
      }
    }

    const userMsg: ChatMessageData = {
      id: `u-${seed}`,
      role: "user",
      content: text + (file ? `\n\n[Attached File: ${file.name}]` : ""),
      time: "now",
    };
    setMessages((m) => [...m, userMsg]);
    setComposerText("");

    const token = session?.token;
    const apiUrl = getStoredApiUrl();

    if (!token) {
      setStreamError("Authentication required. Please log in.");
      return;
    }

    const replyId = `a-${seed}`;
    let fullText = "";

    try {
      setStreamingId(replyId);
      setStreamingText("");
      abortControllerRef.current = new AbortController();

      const payloadContext = uploadedDocId ? { document_ids: [uploadedDocId] } : undefined;

      const streamResult = await streamChat(
        apiUrl,
        token,
        {
          question: text,
          patient_id: patientId,
          context: payloadContext,
        },
        (event) => {
          if (event.type === "token") {
            fullText += event.content || "";
            setStreamingText(fullText);
          }
        },
        abortControllerRef.current.signal,
      );

      // The backend `streamResult.citations` is ordered 1 to N for the current response.
      // We will assign `c.n = index + 1` so that the inline citations `[1]` match the rawCitations array order.
      const reply: ChatMessageData = {
        id: replyId,
        role: "assistant",
        content: fullText || "I couldn't generate a response. Please try again.",
        time: "now",
        rawCitations: streamResult.citations,
        citations: streamResult.citations?.map((c, idx) => ({
          n: idx + 1, // matches backend's inline [1], [2] format
          sourceId: c.evidence_id,
        })),
      };
      setMessages((m) => [...m, reply]);
      setStreamingId(null);
      setStreamingText("");
      return;
    } catch (err: any) {
      console.warn("Backend stream failed:", err);
      if (err.name === "AbortError") {
        setStreamError("Stream stopped by user.");
      } else {
        setStreamError(
          err instanceof Error ? err.message : "Backend stream failed. Please try again.",
        );
      }
      if (fullText) {
        const reply: ChatMessageData = {
          id: replyId,
          role: "assistant",
          content: fullText,
          time: "now",
        };
        setMessages((m) => [...m, reply]);
      }
      setStreamingId(null);
      setStreamingText("");
    } finally {
      abortControllerRef.current = null;
    }
  };

  if (messages.length === 0 && !thread && !patientId) {
    return (
      <AppShell
        rightRail={
          <Card className="p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <Clock className="h-4 w-4 text-muted-foreground" /> Recent threads
            </div>
            <ul className="space-y-1">
              {(backendThreads || []).map((t) => (
                <li key={t.id}>
                  <Link
                    to="/chat"
                    search={(prev) => ({
                      ...prev,
                      patient: t.patient_id ?? undefined,
                      thread: t.id,
                    })}
                    className="block rounded-md p-2 hover:bg-muted"
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ai" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{t.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {t.patient_id ? `Patient context • ` : ""}
                          {t.visibility === "shared" ? "Shared" : "Private"}
                        </p>
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
          <div className="mt-6 w-full text-left">
            <ChatComposer
              value={composerText}
              onValueChange={setComposerText}
              onSend={send}
              contextNode={contextNode}
              allowAttachment={!!patientId}
            />
          </div>
        </div>
      </AppShell>
    );
  }

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
      <div className="space-y-5 pb-6">
        {currentPatient && (
          <Card className="mb-4 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <Heart className="h-4 w-4 text-destructive" />
                  <h2 className="text-lg font-semibold">{currentPatient.full_name}</h2>
                  <Badge variant="secondary" className="bg-success/10 text-success">
                    <ShieldCheck className="mr-1 h-3 w-3" /> Access verified
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {currentPatient.department || "--"} · {currentPatient.status}
                </p>
              </div>
              <div className="text-right text-xs text-muted-foreground">
                <p className="font-mono">{currentPatient.mrn}</p>
              </div>
            </div>
          </Card>
        )}

        {messages.map((m) => (
          <ChatMessage key={m.id} msg={m} />
        ))}
        {streamingId !== null && (
          <div className="rounded-lg bg-muted/50 p-4 text-sm relative border shadow-sm">
            <p className="whitespace-pre-wrap leading-relaxed">
              {streamingText}
              <span className="animate-pulse">▍</span>
            </p>
            <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground border-t pt-2">
              <span className="flex items-center gap-1.5">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-ai" /> Generating response...
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={stopStream}
                className="h-6 px-2 text-[11px] hover:text-destructive hover:bg-destructive/10"
              >
                <Square className="mr-1 h-3 w-3" /> Stop
              </Button>
            </div>
          </div>
        )}
      </div>

      {streamError && <p className="mb-2 text-sm text-destructive">{streamError}</p>}

      <div className="sticky bottom-4">
        <ChatComposer
          value={composerText}
          onValueChange={setComposerText}
          onSend={send}
          contextNode={contextNode}
          disabled={streamingId !== null || streamingText !== ""}
          disabledHint={
            streamingText ? "Receiving response from AI..." : "Waiting for current response…"
          }
          allowAttachment={!!patientId}
        />
      </div>
    </AppShell>
  );
}
