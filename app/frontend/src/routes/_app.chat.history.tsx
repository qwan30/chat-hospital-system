import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { listChatThreads } from "@/lib/api/chat-threads";
import type { ChatThreadRead } from "@/lib/api/chat-threads";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/_app/chat/history")({
  head: () => ({ meta: [{ title: "Chat history — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { data: threadsResult, isLoading } = useQuery({
    queryKey: ["chat-threads"],
    queryFn: () => listChatThreads(),
  });

  const threads = threadsResult || [];

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
              <li key={t.id} className="flex items-center justify-between p-4">
                <div>
                  <p className="text-sm font-medium">{t.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {t.patient_id ? `Patient ${t.patient_id} · ` : ""}
                    {new Date(t.updated_at).toLocaleDateString()}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </AppShell>
  );
}
