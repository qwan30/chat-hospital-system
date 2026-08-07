import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDocument, retryIndex, getDocumentIntelligence } from "@/lib/api/documents";
import { Loader2 } from "lucide-react";
import { DocumentWorkspace } from "@/components/hms/document-workspace/DocumentWorkspace";
import { ErrorState } from "@/components/hms/ErrorState";
import { newIdempotencyKey } from "@/lib/idempotency";

export const Route = createFileRoute("/_app/documents/$documentId")({
  head: () => ({ meta: [{ title: "Document — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { documentId } = Route.useParams();
  const queryClient = useQueryClient();

  const {
    data: d,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "uploaded" || status === "ocr_processing" || status === "indexing") {
        return 2000;
      }
      return false;
    },
  });

  const { data: intelligence } = useQuery({
    queryKey: ["document-intelligence", documentId],
    queryFn: () => getDocumentIntelligence(documentId),
    enabled: !!d && d.status === "indexed",
  });

  const retryMutation = useMutation({
    mutationFn: () => retryIndex(documentId, { idempotencyKey: newIdempotencyKey("retry-index") }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex h-[50vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </AppShell>
    );
  }

  if (error || !d) {
    return (
      <AppShell>
        <div className="p-8">
          <ErrorState
            title="Failed to load document"
            description={error instanceof Error ? error.message : "Document not found"}
            code="DOC_ERR"
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title={d.title}
        description={`${d.document_type} · ${d.page_count || 0} pages`}
        backLink={{ to: "/documents", label: "Back to Documents" }}
        chips={
          <Badge variant="secondary" className="capitalize">
            {d.status}
          </Badge>
        }
        actions={
          <div className="flex gap-2">
            {intelligence?.review_items_count ? (
              <Button asChild variant="default">
                <Link to="/documents/$documentId/review" params={{ documentId }}>
                  Review {intelligence.review_items_count} items
                </Link>
              </Button>
            ) : null}
            <Button
              variant="outline"
              onClick={() => retryMutation.mutate()}
              disabled={retryMutation.isPending}
            >
              {retryMutation.isPending ? "Retrying..." : "Retry Indexing"}
            </Button>
          </div>
        }
      />
      <div className="flex-1 overflow-hidden">
        <DocumentWorkspace documentId={documentId} />
      </div>
    </AppShell>
  );
}
