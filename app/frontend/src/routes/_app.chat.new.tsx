import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { searchPatients } from "@/lib/api/patients";
import { useState } from "react";
import { StatusBadge } from "@/components/hms/StatusBadge";
import { useQuery } from "@tanstack/react-query";

export const Route = createFileRoute("/_app/chat/new")({
  head: () => ({ meta: [{ title: "New chat — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const [q, setQ] = useState("");

  const { data: searchResponse, isLoading } = useQuery({
    queryKey: ["patients", q],
    queryFn: () => searchPatients(q || undefined, 20),
  });

  const filtered = searchResponse?.items || [];

  return (
    <AppShell>
      <PageHeader
        title="Start a new chat"
        description="Pick a patient context, or start a general clinical chat."
      />
      <Card className="p-4">
        <Input
          placeholder="Search patients by name or MRN…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </Card>
      <div className="mt-4 grid gap-2">
        {isLoading && <div className="text-sm text-muted-foreground p-2">Searching...</div>}
        {filtered.map((p) => (
          <Link
            key={p.id}
            to="/chat"
            search={{ patient: p.id }}
            className="flex items-center justify-between rounded-md border bg-card p-3 hover:bg-muted"
          >
            <div>
              <p className="font-medium text-sm">{p.full_name}</p>
              <p className="text-xs text-muted-foreground">{p.department || "No department"}</p>
            </div>
            <StatusBadge status="allow" />
          </Link>
        ))}
      </div>
      <Card className="mt-4 p-4 text-sm">
        <Link to="/chat" className="text-primary underline">
          Or start a general clinical knowledge chat →
        </Link>
      </Card>
    </AppShell>
  );
}
