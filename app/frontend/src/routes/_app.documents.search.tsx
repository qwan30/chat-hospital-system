import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { searchDocuments, type DocumentSearchRequest } from "@/lib/api/documents";
import { Loader2 } from "lucide-react";
import { z } from "zod";

const searchSchema = z.object({
  q: z.string().optional(),
  patientId: z.string().optional(),
});

export function canSearchDocuments(query: string, patientId: string): boolean {
  return Boolean(query.trim() && patientId.trim());
}

export function submitDocumentSearch(
  mutate: (payload: DocumentSearchRequest) => void,
  query: string,
  patientId: string,
): boolean {
  if (!canSearchDocuments(query, patientId)) return false;

  mutate({
    patient_id: patientId.trim(),
    query: query.trim(),
    top_k: 5,
  });
  return true;
}

export const Route = createFileRoute("/_app/documents/search")({
  validateSearch: (search) => searchSchema.parse(search),
  head: () => ({ meta: [{ title: "Search documents — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const searchParams = Route.useSearch();
  const [patientId, setPatientId] = useState(searchParams.patientId || "");
  const [q, setQ] = useState(searchParams.q || "");

  const searchMutation = useMutation({
    mutationFn: searchDocuments,
  });

  const { mutate } = searchMutation;
  const canSearch = canSearchDocuments(q, patientId);

  useEffect(() => {
    setPatientId(searchParams.patientId || "");
    setQ(searchParams.q || "");
  }, [searchParams.patientId, searchParams.q]);

  useEffect(() => {
    submitDocumentSearch(mutate, searchParams.q || "", searchParams.patientId || "");
  }, [searchParams.q, searchParams.patientId, mutate]);

  return (
    <AppShell>
      <PageHeader
        title="Document search"
        description="Hybrid keyword + vector search within this patient's authorized documents."
      />
      <Card className="p-3">
        <div className="flex gap-2">
          <Input
            placeholder="Patient UUID"
            className="w-1/3"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
          />
          <Input
            placeholder="Search query..."
            className="flex-1"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && canSearch) {
                submitDocumentSearch(mutate, q, patientId);
              }
            }}
          />
          <Button
            onClick={() => submitDocumentSearch(mutate, q, patientId)}
            disabled={searchMutation.isPending || !canSearch}
          >
            {searchMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
          </Button>
        </div>
        {!patientId.trim() && (
          <p className="mt-2 text-xs text-muted-foreground">
            Enter a Patient UUID to search only documents you are authorized to access.
          </p>
        )}
      </Card>

      {searchMutation.error && (
        <div className="mt-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {searchMutation.error instanceof Error ? searchMutation.error.message : "Search failed"}
        </div>
      )}

      <div className="mt-4 space-y-2">
        {searchMutation.data?.items.map((d, i) => (
          <Card key={d.chunk_id} className="p-4">
            <p className="text-sm font-semibold">{d.document_title}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Page {d.page} · score {d.score.toFixed(3)} · Chunk ID: {d.chunk_id.substring(0, 8)}
            </p>
            <p className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap">
              {d.content || "No text available"}
            </p>
          </Card>
        ))}
        {searchMutation.data?.items.length === 0 && (
          <p className="text-sm text-muted-foreground mt-4 text-center">No results found.</p>
        )}
      </div>
    </AppShell>
  );
}
