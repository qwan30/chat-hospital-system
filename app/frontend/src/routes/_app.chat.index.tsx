import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { z } from "zod";
import { AppShell } from "@/components/shell/AppShell";
import { Card } from "@/components/ui/card";
import { ChatComposer } from "@/components/hms/ChatComposer";
import { Logo } from "@/components/hms/Logo";
import {
  Clock,
  MessageSquare,
  Sparkles,
  Heart,
  ShieldCheck,
  Pin,
  PinOff,
  Edit2,
  Check,
} from "lucide-react";
import { useState, useMemo, useEffect } from "react";
import { ChatMessage, type ChatMessageData } from "@/components/hms/ChatMessage";
import { EvidenceRail, type EvidenceItem } from "@/components/hms/EvidenceRail";
import { SafeRefusalCard } from "@/components/hms/SafeRefusalCard";
import { Badge, badgeVariants } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ErrorState } from "@/components/hms/ErrorState";
import { sanitizeError } from "@/lib/errors";
import { searchPatients, getPatient } from "@/lib/api/patients";
import { useSession } from "@/lib/session";
import { streamChat, type StreamStatusStage } from "@/lib/stream-client";
import {
  hasStreamScopeChanged,
  isCurrentStreamRequest,
  type StreamScope,
} from "@/lib/stream-scope";
import { getStoredApiUrl } from "@/lib/api-client";
import { uploadDocument } from "@/lib/api/documents";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import {
  listChatThreads,
  createChatThread,
  getChatThread,
  updateChatThread,
} from "@/lib/api/chat-threads";
import { formatDistanceToNow } from "date-fns";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { ChevronDown, X, AlertTriangle, Loader2, Square, ArrowLeft } from "lucide-react";
import { useRef } from "react";
import { StreamingControls } from "@/components/hms/StreamingControls";

const chatSearchSchema = z.object({
  patient: z.string().optional(),
  thread: z.string().optional(),
  q: z.string().optional(),
  simulate: z.string().optional(),
});

const parseUtcDate = (dateStr: string | Date | undefined): Date => {
  if (!dateStr) return new Date();
  if (dateStr instanceof Date) return dateStr;
  let formatted = dateStr;
  if (
    typeof formatted === "string" &&
    formatted.includes("T") &&
    !formatted.endsWith("Z") &&
    !/[-+]\d{2}:?\d{2}$/.test(formatted)
  ) {
    formatted = formatted + "Z";
  }
  return new Date(formatted);
};

export const Route = createFileRoute("/_app/chat/")({
  validateSearch: chatSearchSchema,
  head: () => ({
    meta: [
      { title: "Chat — HMS AI Copilot" },
      { name: "description", content: "Ask the hospital knowledge assistant." },
    ],
  }),
  component: GlobalChat,
  errorComponent: ({ error, reset }) => (
    <AppShell fixedHeight>
      <div className="flex h-full items-center justify-center p-8">
        <ErrorState
          title="Failed to load chat"
          description={sanitizeError(error)}
          code="API_ERROR"
          extra={
            <Button onClick={reset} variant="outline">
              Retry
            </Button>
          }
        />
      </div>
    </AppShell>
  ),
});

const suggestions = [
  "DAPT guideline duration for post-PCI patients",
  "Sepsis 1-hour bundle requirements and lactate triggers",
  "DOAC dosing adjustments for renal impairment",
  "Initial assessment protocol for acute dyspnea",
];

const streamStageLabel: Record<StreamStatusStage, string> = {
  retrieving: "Retrieving relevant evidence…",
  preparing_answer: "Preparing answer…",
  validating_citations: "Validating citations…",
  complete: "Answer ready",
};

function GlobalChat() {
  const { patient: patientId, thread, q: initialQ, simulate } = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const { session } = useSession();

  const [composerText, setComposerText] = useState("");
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [lastQuestion, setLastQuestion] = useState("");
  const lastQuestionRef = useRef("");
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [streamError, setStreamError] = useState<string | null>(null);
  const [streamStage, setStreamStage] = useState<StreamStatusStage | null>(null);
  const [attachmentStatus, setAttachmentStatus] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeStreamScopeRef = useRef<StreamScope | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const createdThreadIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages, streamingText]);

  const stopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const queryClient = useQueryClient();

  const { data: backendThreads } = useQuery({
    queryKey: ["chat-threads"],
    queryFn: listChatThreads,
    enabled: !!session?.token,
  });

  const [pinnedThreadIds, setPinnedThreadIds] = useState<string[]>([]);
  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);
  const [editTitleVal, setEditTitleVal] = useState("");
  const [patientSearchQuery, setPatientSearchQuery] = useState("");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("pinned_threads");
      if (stored) {
        setPinnedThreadIds(JSON.parse(stored));
      }
    } catch (e) {
      console.error("Failed to load pinned threads", e);
    }
  }, []);

  const togglePinThread = (threadId: string) => {
    const nextPinned = pinnedThreadIds.includes(threadId)
      ? pinnedThreadIds.filter((id) => id !== threadId)
      : [...pinnedThreadIds, threadId];
    setPinnedThreadIds(nextPinned);
    try {
      localStorage.setItem("pinned_threads", JSON.stringify(nextPinned));
    } catch (e) {
      console.error("Failed to save pinned threads", e);
    }
  };

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => updateChatThread(id, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-threads"] });
      setEditingThreadId(null);
    },
  });

  const { pinnedThreads, unpinnedThreads } = useMemo(() => {
    const threads = backendThreads || [];
    const pinned = threads.filter((t) => pinnedThreadIds.includes(t.id));
    const unpinned = threads.filter((t) => !pinnedThreadIds.includes(t.id));
    return { pinnedThreads: pinned, unpinnedThreads: unpinned };
  }, [backendThreads, pinnedThreadIds]);

  const sortedDropdownThreads = useMemo(() => {
    const threads = backendThreads || [];
    return [...threads].sort((a, b) => {
      const aPinned = pinnedThreadIds.includes(a.id);
      const bPinned = pinnedThreadIds.includes(b.id);
      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;
      return parseUtcDate(b.created_at).getTime() - parseUtcDate(a.created_at).getTime();
    });
  }, [backendThreads, pinnedThreadIds]);

  const { data: threadDetail } = useQuery({
    queryKey: ["chat-thread", thread],
    queryFn: () => getChatThread(thread!),
    enabled: !!thread && !!session?.token,
  });

  useEffect(() => {
    if (threadDetail?.messages) {
      if (createdThreadIdRef.current === thread) {
        return;
      }
      const mapped = threadDetail.messages.map((m) => ({
        id: m.id,
        role: m.role as "user" | "assistant",
        content: m.content,
        time: parseUtcDate(m.created_at).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        rawCitations: m.citations.map((c) => ({
          evidence_id: c.evidence_id || (c as any).id,
          document_id: c.document_id,
          document_title: c.document_title || (c as any).source || "Unknown Document",
          page: c.page || 1,
          score: c.score || (c as any).relevance || 0.5,
          content: c.content || (c as any).snippet || "",
        })),
        citations: m.citations.map((c, idx) => ({
          n: idx + 1,
          sourceId: c.evidence_id || (c as any).id,
        })),
      }));
      setMessages(mapped);
    } else {
      if (!thread) {
        setMessages([]);
      }
    }
  }, [threadDetail, thread]);

  useEffect(() => {
    if (!thread) {
      createdThreadIdRef.current = null;
    }
  }, [thread]);

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

  const filteredPatients = useMemo(() => {
    const patientsList = searchResponse?.items || [];
    const query = patientSearchQuery.trim().toLowerCase();
    if (!query) return patientsList;
    return patientsList.filter(
      (p) =>
        p.full_name.toLowerCase().includes(query) ||
        (p.mrn && p.mrn.toLowerCase().includes(query)) ||
        (p.department && p.department.toLowerCase().includes(query)),
    );
  }, [searchResponse?.items, patientSearchQuery]);

  const activeThread = useMemo(() => {
    if (!thread) return null;
    return (backendThreads || []).find((t) => t.id === thread);
  }, [thread, backendThreads]);

  const activeThreadTitle = useMemo(() => {
    if (activeThread) return activeThread.title;
    if (currentPatient) return `Patient Context: ${currentPatient.full_name}`;
    return "General hospital knowledge";
  }, [activeThread, currentPatient]);

  const renderThreadItem = (t: any, isPinned: boolean) => {
    const isEditing = editingThreadId === t.id;

    // Display relative time
    let relativeTime = "";
    try {
      if (t.created_at) {
        relativeTime = formatDistanceToNow(parseUtcDate(t.created_at), { addSuffix: true });
      }
    } catch (e) {
      console.error(e);
    }

    if (isEditing) {
      return (
        <li key={t.id} className="rounded-md bg-muted/50 p-2 border border-border/60">
          <div
            className="flex flex-col gap-2"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
            }}
          >
            <input
              type="text"
              value={editTitleVal}
              onChange={(e) => setEditTitleVal(e.target.value)}
              className="w-full text-sm px-2 py-1 bg-background border border-input rounded-md focus:outline-none focus:ring-1 focus:ring-ai text-foreground"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  if (editTitleVal.trim()) {
                    renameMutation.mutate({ id: t.id, title: editTitleVal.trim() });
                  }
                } else if (e.key === "Escape") {
                  setEditingThreadId(null);
                }
              }}
            />
            <div className="flex items-center justify-end gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs hover:bg-muted cursor-pointer"
                onClick={() => setEditingThreadId(null)}
              >
                <X className="h-3.5 w-3.5 mr-1" /> Cancel
              </Button>
              <Button
                size="sm"
                className="h-7 px-2 text-xs bg-ai hover:bg-ai-hover text-white cursor-pointer"
                disabled={renameMutation.isPending || !editTitleVal.trim()}
                onClick={() => {
                  if (editTitleVal.trim()) {
                    renameMutation.mutate({ id: t.id, title: editTitleVal.trim() });
                  }
                }}
              >
                {renameMutation.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin mr-1" />
                ) : (
                  <Check className="h-3.5 w-3.5 mr-1" />
                )}
                Save
              </Button>
            </div>
          </div>
        </li>
      );
    }

    return (
      <li key={t.id} className="group relative rounded-md hover:bg-muted/80 transition-colors">
        <Link
          to="/chat"
          search={(prev) => ({
            ...prev,
            patient: t.patient_id ?? undefined,
            thread: t.id,
          })}
          className="block p-2 pr-16"
        >
          <div className="flex items-start gap-2">
            {isPinned ? (
              <Pin className="mt-1 h-3.5 w-3.5 shrink-0 text-ai rotate-45 fill-ai" />
            ) : (
              <MessageSquare className="mt-1 h-3.5 w-3.5 shrink-0 text-ai" />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-foreground">{t.title}</p>
              <div className="flex items-center gap-1.5 flex-wrap mt-0.5">
                {t.patient_id && (
                  <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                    Patient Context
                  </span>
                )}
                {relativeTime && (
                  <span className="text-[10px] text-muted-foreground/80">{relativeTime}</span>
                )}
              </div>
            </div>
          </div>
        </Link>

        {/* Hover Actions */}
        <div className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-muted-foreground/10 cursor-pointer"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setEditingThreadId(t.id);
              setEditTitleVal(t.title);
            }}
            title="Rename session"
          >
            <Edit2 className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "h-7 w-7 cursor-pointer",
              isPinned
                ? "text-ai hover:text-ai/80 hover:bg-ai/10"
                : "text-muted-foreground hover:text-foreground hover:bg-muted-foreground/10",
            )}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              togglePinThread(t.id);
            }}
            title={isPinned ? "Unpin session" : "Pin session"}
          >
            {isPinned ? (
              <PinOff className="h-3.5 w-3.5" />
            ) : (
              <Pin className="h-3.5 w-3.5 rotate-45" />
            )}
          </Button>
        </div>
      </li>
    );
  };

  const contextNode = (
    <div className="flex items-center gap-1">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            className={cn(
              badgeVariants({ variant: "secondary" }),
              "cursor-pointer bg-primary/10 text-primary hover:bg-primary/20",
            )}
          >
            <Sparkles className="mr-1 h-3 w-3" />
            {currentPatient
              ? `Context: Patient — ${currentPatient.full_name}`
              : "Context: General hospital knowledge"}
            <ChevronDown className="ml-1 h-3 w-3" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          className="w-[300px] max-h-[300px] overflow-hidden flex flex-col p-1"
        >
          <div
            className="px-2 py-1.5 shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
            }}
          >
            <input
              type="text"
              placeholder="Search patient by name or MRN..."
              value={patientSearchQuery}
              onChange={(e) => setPatientSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                e.stopPropagation();
              }}
              className="w-full text-xs px-2.5 py-1.5 bg-background border border-input rounded-md focus:outline-none focus:ring-1 focus:ring-ai text-foreground placeholder:text-muted-foreground/60"
            />
          </div>
          <DropdownMenuSeparator className="my-1 shrink-0" />
          <div className="flex-1 overflow-y-auto space-y-0.5 max-h-[220px]">
            <DropdownMenuItem
              onClick={() => {
                navigate({ search: (prev) => ({ ...prev, patient: undefined }) });
                setPatientSearchQuery("");
              }}
            >
              General hospital knowledge
            </DropdownMenuItem>
            {filteredPatients.length === 0 ? (
              <div className="p-4 text-center text-xs text-muted-foreground">No patients found</div>
            ) : (
              filteredPatients.map((p) => (
                <DropdownMenuItem
                  key={p.id}
                  onClick={() => {
                    navigate({ search: (prev) => ({ ...prev, patient: p.id }) });
                    setPatientSearchQuery("");
                  }}
                >
                  <div className="flex flex-col w-full text-left">
                    <div className="flex justify-between">
                      <span className="font-medium">{p.full_name}</span>
                    </div>
                    <span className="text-[10px] text-muted-foreground">
                      {p.mrn} - {p.department || "--"}
                    </span>
                  </div>
                </DropdownMenuItem>
              ))
            )}
          </div>
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
            page: c.page || 1,
          });
        }
      });
    });
    return items;
  }, [messages]);

  const noEvidence = evidence.length === 0 && messages.length === 0;

  const handleRetry = () => {
    setMessages((m) => m.slice(0, -1));
    send(lastQuestionRef.current);
  };

  const handleResume = () => {
    setMessages((m) => m.slice(0, -1));
    send(lastQuestionRef.current);
  };

  const send = async (text: string, file?: File) => {
    const seed = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

    lastQuestionRef.current = text;
    setLastQuestion(text);
    setStreamError(null);
    setStreamStage(null);
    setAttachmentStatus(null);
    let uploadedDocId: string | undefined;
    const uploadPatientId = file ? patientId : undefined;
    const token = session?.token;
    const apiUrl = getStoredApiUrl();

    if (!token) {
      setStreamError("Authentication required. Please log in.");
      return;
    }

    if (file) {
      if (!uploadPatientId) {
        setStreamError("A patient context is required to upload a document.");
        return;
      }
    }

    const requestController = new AbortController();
    abortControllerRef.current = requestController;
    activeStreamScopeRef.current = { patientId, threadId: thread };
    const isActiveRequest = () =>
      isCurrentStreamRequest(abortControllerRef.current, requestController);

    if (file && uploadPatientId) {
      try {
        setAttachmentStatus(`Uploading ${file.name}…`);
        const doc = await uploadDocument(uploadPatientId, file.name, "Chat Attachment", file);
        if (!isActiveRequest()) return;
        uploadedDocId = doc.id;
        setAttachmentStatus(`${file.name} attached for this answer.`);
      } catch (err) {
        if (isActiveRequest()) {
          setStreamError("Failed to upload the document. Please try again.");
          abortControllerRef.current = null;
          activeStreamScopeRef.current = null;
        }
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

    const replyId = `a-${seed}`;
    let fullText = "";

    try {
      setStreamingId(replyId);
      setStreamingText("");

      const payloadContext = uploadedDocId ? { document_ids: [uploadedDocId] } : undefined;

      let activeThreadId = thread;
      if (!activeThreadId) {
        try {
          const newThread = await createChatThread({
            scope: patientId ? "patient-linked" : "general",
            patient_id: patientId ?? null,
            title: text.substring(0, 50) || "New chat",
          });
          if (!isActiveRequest()) return;
          activeThreadId = newThread.id;
          createdThreadIdRef.current = newThread.id;
          activeStreamScopeRef.current = { patientId, threadId: newThread.id };
          navigate({
            search: (prev) => ({ ...prev, thread: newThread.id }),
            replace: true,
          });
          queryClient.invalidateQueries({ queryKey: ["chat-threads"] });
        } catch (err) {
          console.error("Failed to create chat thread:", err);
        }
      }

      if (!isActiveRequest()) return;

      const streamResult = await streamChat(
        apiUrl,
        token,
        {
          question: text,
          patient_id: patientId,
          thread_id: activeThreadId,
          context: payloadContext,
        },
        (event) => {
          if (!isActiveRequest()) return;
          if (event.type === "status" && event.stage) {
            setStreamStage(event.stage);
            return;
          }
          if (event.type === "token") {
            fullText += event.content || "";
            setStreamingText(fullText);
            if (simulate === "stream-fail" && fullText.length > 30) {
              requestController?.abort();
            }
          }
        },
        requestController.signal,
      );

      if (!isActiveRequest()) return;

      if (streamResult.error) {
        setStreamError(streamResult.error);
        setStreamingId(null);
        setStreamingText("");
        return;
      }

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
      setStreamStage(null);
      if (activeThreadId) {
        queryClient.invalidateQueries({ queryKey: ["chat-thread", activeThreadId] });
        queryClient.invalidateQueries({ queryKey: ["chat-threads"] });
      }
      return;
    } catch (err: any) {
      if (!isCurrentStreamRequest(abortControllerRef.current, requestController)) return;
      console.warn("Backend stream failed:", err);
      const isSimulated = simulate === "stream-fail" && err.name === "AbortError";
      if (err.name === "AbortError" && !isSimulated) {
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
          extra: isSimulated ? (
            <StreamingControls
              status="interrupted"
              error="The stream was interrupted during simulation."
              progress={40}
              total={100}
              onRetry={handleRetry}
              onResume={handleResume}
              onStop={stopStream}
            />
          ) : undefined,
        };
        setMessages((m) => [...m, reply]);
      }
      setStreamingId(null);
      setStreamingText("");
    } finally {
      if (abortControllerRef.current === requestController) {
        abortControllerRef.current = null;
        activeStreamScopeRef.current = null;
      }
    }
  };

  useEffect(() => {
    if (initialQ) {
      send(initialQ);
      navigate({ search: (prev) => ({ ...prev, q: undefined }), replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQ]);

  useEffect(() => {
    const activeScope = activeStreamScopeRef.current;
    if (activeScope && hasStreamScopeChanged(activeScope, { patientId, threadId: thread })) {
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      activeStreamScopeRef.current = null;
    }
  }, [patientId, thread]);

  useEffect(() => {
    return () => abortControllerRef.current?.abort();
  }, []);

  if (messages.length === 0 && !thread && !patientId) {
    return (
      <AppShell
        fixedHeight={true}
        rightRail={
          <Card className="p-4 h-full flex flex-col overflow-hidden">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold shrink-0">
              <Clock className="h-4 w-4 text-muted-foreground" /> Recent threads
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {pinnedThreads.length > 0 && (
                <div>
                  <div className="mb-1 flex items-center gap-1.5 px-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    <Pin className="h-3 w-3 fill-ai text-ai rotate-45" /> Pinned
                  </div>
                  <ul className="space-y-1">
                    {pinnedThreads.map((t) => renderThreadItem(t, true))}
                  </ul>
                </div>
              )}

              <div>
                {pinnedThreads.length > 0 && (
                  <div className="mb-1.5 flex items-center gap-1.5 px-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Recent
                  </div>
                )}
                <ul className="space-y-1">
                  {unpinnedThreads.length === 0 && pinnedThreads.length === 0 ? (
                    <li className="p-4 text-center text-xs text-muted-foreground">
                      No previous sessions
                    </li>
                  ) : (
                    unpinnedThreads.map((t) => renderThreadItem(t, false))
                  )}
                </ul>
              </div>
            </div>
          </Card>
        }
      >
        <div className="flex flex-col h-full overflow-hidden">
          <div className="flex-1 overflow-y-auto pr-2">
            <div className="mx-auto flex max-w-3xl flex-col items-center pt-10 text-center">
              <Logo size={56} />
              <h1 className="mt-5 text-3xl font-semibold tracking-tight">General clinical chat</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                Cited answers from your hospital's indexed knowledge base. PHI-safe and
                audit-logged.
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
            </div>
          </div>
          <div className="border-t bg-background pt-4 pb-2 w-full text-left">
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
      fixedHeight={true}
      rightRail={
        noEvidence ? (
          <SafeRefusalCard reason="Ask a question to retrieve evidence from indexed sources." />
        ) : (
          <Card className="p-4 h-full flex flex-col bg-card border-border/80 shadow-sm overflow-y-auto">
            <EvidenceRail items={evidence} />
          </Card>
        )
      }
    >
      <div className="flex flex-col h-full overflow-hidden">
        {/* Chat Header */}
        <div className="flex items-center justify-between border-b pb-3 mb-4 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0 hover:bg-muted cursor-pointer"
              onClick={() => navigate({ search: () => ({}) })}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div className="flex flex-col min-w-0">
              <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Active Session
              </span>
              <h2 className="text-sm font-semibold truncate text-foreground/90">
                {activeThreadTitle}
              </h2>
            </div>
          </div>

          {/* Session History Dropdown Button */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="gap-1 shadow-sm shrink-0 cursor-pointer"
              >
                <Clock className="h-3.5 w-3.5" />
                <span>History</span>
                <ChevronDown className="h-3.5 w-3.5 opacity-60" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="w-[280px] max-h-[300px] overflow-y-auto p-1 animate-in fade-in-50 slide-in-from-top-1 duration-200"
            >
              <DropdownMenuLabel className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                Recent Chats
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {!sortedDropdownThreads || sortedDropdownThreads.length === 0 ? (
                <div className="p-4 text-center text-xs text-muted-foreground">
                  No previous sessions
                </div>
              ) : (
                sortedDropdownThreads.map((t) => {
                  const isPinned = pinnedThreadIds.includes(t.id);
                  let relativeTime = "";
                  try {
                    if (t.created_at) {
                      relativeTime = formatDistanceToNow(parseUtcDate(t.created_at), {
                        addSuffix: true,
                      });
                    }
                  } catch (e) {
                    console.error(e);
                  }
                  return (
                    <DropdownMenuItem key={t.id} className="p-0 cursor-pointer">
                      <Link
                        to="/chat"
                        search={(prev) => ({
                          ...prev,
                          patient: t.patient_id ?? undefined,
                          thread: t.id,
                        })}
                        className="flex items-start gap-2 w-full p-2 text-left hover:bg-accent transition-colors"
                      >
                        {isPinned ? (
                          <Pin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ai rotate-45 fill-ai" />
                        ) : (
                          <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ai" />
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{t.title}</p>
                          <div className="flex items-center gap-1.5 flex-wrap mt-0.5">
                            <span className="text-[9px] text-muted-foreground/80">
                              {t.patient_id ? "Patient context" : "General context"}
                            </span>
                            {relativeTime && (
                              <span className="text-[9px] text-muted-foreground/60">
                                • {relativeTime}
                              </span>
                            )}
                          </div>
                        </div>
                      </Link>
                    </DropdownMenuItem>
                  );
                })
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto space-y-5 pr-2 pb-4">
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
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-ai" />{" "}
                  {streamStage ? streamStageLabel[streamStage] : "Generating response..."}
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

          {streamError && <p className="mb-2 text-sm text-destructive">{streamError}</p>}
        </div>

        <div className="border-t bg-background pt-4 pb-2">
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
            attachmentStatus={attachmentStatus}
          />
        </div>
      </div>
    </AppShell>
  );
}
