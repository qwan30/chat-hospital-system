import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listChatThreads, deleteChatThread } from "@/lib/api/chat-threads";
import type { ChatThreadRead } from "@/lib/api/chat-threads";
import { Loader2, Trash2, MessageSquare } from "lucide-react";

export const Route = createFileRoute("/_app/chat/history")({
  head: () => ({ meta: [{ title: "Chat history — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const queryClient = useQueryClient();
  const { data: threadsResult, isLoading } = useQuery({
    queryKey: ["chat-threads"],
    queryFn: () => listChatThreads(),
  });

  const deleteMutation = useMutation({
    mutationFn: (threadId: string) => deleteChatThread(threadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-threads"] });
    },
  });

  const threads = (threadsResult || []).filter((t: ChatThreadRead) => t.status !== "archived");

  const handleDelete = (e: React.MouseEvent, threadId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm("Are you sure you want to archive and remove this chat session?")) {
      deleteMutation.mutate(threadId);
    }
  };

  return (
    <AppShell>
      <PageHeader title="Chat history" description="Audited transcripts of your past sessions." />
      <Card className="p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <ul className="divide-y">
            {threads.length === 0 && (
              <li className="p-8 text-center text-sm text-muted-foreground">
                No chat history found.
              </li>
            )}
            {threads.map((t: ChatThreadRead) => (
              <li
                key={t.id}
                className="flex items-center justify-between p-4 hover:bg-muted/40 transition-colors"
              >
                <Link
                  to="/chat"
                  search={{ thread: t.id, patient: t.patient_id || undefined }}
                  className="flex items-center gap-3 flex-1 min-w-0 pr-4"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary shrink-0">
                    <MessageSquare className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">
                      {t.title || "Untitled chat session"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {t.patient_id ? `Patient ${t.patient_id} · ` : "General · "}
                      {new Date(t.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0"
                  onClick={(e) => handleDelete(e, t.id)}
                  disabled={deleteMutation.isPending}
                  title="Delete chat session"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </AppShell>
  );
}
