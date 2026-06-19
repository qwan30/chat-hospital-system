import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { threads } from "@/data/threads";

export const Route = createFileRoute("/_app/chat/history")({
  head: () => ({ meta: [{ title: "Chat history — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Chat history" description="Audited transcripts of your past sessions." />
      <Card className="p-0 overflow-hidden">
        <ul className="divide-y">
          {threads.map((t) => (
            <li key={t.id} className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-medium">{t.title}</p>
                <p className="text-xs text-muted-foreground">
                  {t.patientId ? `Patient ${t.patientId} · ` : ""}
                  {t.updated}
                </p>
              </div>
              <span className="text-xs text-muted-foreground">{t.messages.length} messages</span>
            </li>
          ))}
        </ul>
      </Card>
    </AppShell>
  );
}
