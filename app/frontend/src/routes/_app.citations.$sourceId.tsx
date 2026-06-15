import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Download, ExternalLink, FileText } from "lucide-react";
import { citations, citationList } from "@/data/citations";

export const Route = createFileRoute("/_app/citations/$sourceId")({
  head: () => ({
    meta: [{ title: "Citation — HMS AI Copilot" }],
  }),
  component: CitationPage,
});

function CitationPage() {
  const { sourceId } = Route.useParams();
  const c = citations[sourceId] ?? citationList[0];

  return (
    <AppShell
      rightRail={
        <Card className="p-4">
          <h3 className="text-sm font-semibold">Other cited sources</h3>
          <ul className="mt-3 space-y-2">
            {citationList
              .filter((s) => s.id !== c.id)
              .map((s) => (
                <li key={s.id}>
                  <Link
                    to="/citations/$sourceId"
                    params={{ sourceId: s.id }}
                    className="block rounded-md border p-2 hover:bg-muted"
                  >
                    <p className="line-clamp-1 text-sm font-medium">{s.title}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{s.type} · {s.date}</p>
                  </Link>
                </li>
              ))}
          </ul>
        </Card>
      }
    >
      <Button asChild variant="ghost" size="sm" className="-ml-2 mb-3">
        <Link to="/chat"><ArrowLeft className="mr-1 h-3.5 w-3.5" /> Back to chat</Link>
      </Button>
      <Card className="overflow-hidden p-0">
        <div className="border-b p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <Badge variant="secondary" className="bg-citation/10 text-citation">
                {c.type}
              </Badge>
              <h1 className="mt-2 text-xl font-semibold leading-tight">{c.title}</h1>
              <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                <FileText className="h-3.5 w-3.5" /> {c.source} · {c.date}
                {c.page ? <span>· p.{c.page}</span> : null}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Download className="mr-1 h-3.5 w-3.5" /> Download
              </Button>
              <Button size="sm">
                <ExternalLink className="mr-1 h-3.5 w-3.5" /> Open original
              </Button>
            </div>
          </div>
        </div>
        <div className="p-5">
          <div className="rounded-lg border-l-4 border-citation bg-citation/5 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-citation">
              Cited passage
            </p>
            <p className="mt-2 text-base font-medium leading-relaxed">"{c.snippet}"</p>
          </div>
          <div className="mt-5 space-y-3 text-sm leading-relaxed text-muted-foreground">
            <h3 className="text-sm font-semibold text-foreground">Full passage</h3>
            <p>{c.body}</p>
            <p className="rounded-md border bg-muted/40 p-3 text-xs">
              <span className="font-semibold text-foreground">Provenance:</span> This document is
              part of the hospital's indexed knowledge base. Retrieval relevance for the cited
              query: <span className="font-mono">{(c.relevance * 100).toFixed(0)}%</span>.
            </p>
          </div>
        </div>
      </Card>
    </AppShell>
  );
}