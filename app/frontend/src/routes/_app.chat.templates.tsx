import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { promptTemplates } from "@/data/templates";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/chat/templates")({
  head: () => ({ meta: [{ title: "Chat templates — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  return (
    <AppShell>
      <PageHeader title="Prompt templates" description="Reusable clinical prompts curated by your specialty." />
      <div className="grid gap-3 md:grid-cols-2">
        {promptTemplates.map(t=>(<Card key={t.id} className="p-4"><div className="flex items-start justify-between"><div><p className="text-sm font-semibold">{t.title}</p><p className="mt-1 text-xs text-muted-foreground">{t.category} · used {t.usage}×</p></div><Button size="sm" variant="outline">Use</Button></div><p className="mt-3 text-sm">{t.body}</p></Card>))}
      </div>
    </AppShell>
  );
}
