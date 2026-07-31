import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery, useQueries, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getDocument,
  getDocumentPage,
  retryIndex,
  getDocumentIntelligence,
} from "@/lib/api/documents";
import { Loader2 } from "lucide-react";
import { ErrorState } from "@/components/hms/ErrorState";
import { DocumentPreview } from "@/components/hms/DocumentPreview";
import { DocumentProcessingTimeline } from "@/components/hms/DocumentProcessingTimeline";
import { TypewriterText } from "@/components/ui/typewriter";

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

  const pageQueries = useQueries({
    queries: Array.from({ length: d?.page_count || 0 }).map((_, i) => ({
      queryKey: ["document-page", documentId, i + 1],
      queryFn: () => getDocumentPage(documentId, i + 1),
      enabled: !!d && d.status === "indexed",
    })),
  });

  const pagesLoading = pageQueries.some((q) => q.isLoading);
  const allPagesText = pageQueries
    .map((q) => q.data?.ocr_text)
    .filter(Boolean)
    .join("\n\n---\n\n");

  const retryMutation = useMutation({
    mutationFn: () => retryIndex(documentId),
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
      <div className="grid gap-4">
        {/* Top Section: Context (Metadata & Timeline) */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="p-4 md:col-span-1 flex flex-col justify-center space-y-2 text-xs">
            <Row k="Uploaded" v={new Date(d.created_at).toLocaleString()} />
            <Row k="By" v={d.uploaded_by.substring(0, 8)} />
            <Row k="Patient" v={d.patient_id.substring(0, 8)} />
            <Row k="Type" v={d.mime_type.split("/").pop()?.toUpperCase() || d.mime_type} />
            {d.ocr_error && <Row k="OCR Error" v={d.ocr_error} />}
            {pageQueries[0]?.data?.ocr_confidence !== undefined &&
              pageQueries[0]?.data?.ocr_confidence !== null && (
                <Row
                  k="OCR Confidence"
                  v={`${Math.round(pageQueries[0].data.ocr_confidence * 100)}%`}
                />
              )}
          </Card>

          <Card className="p-4 md:col-span-2 flex flex-col justify-center overflow-hidden">
            <h4 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Processing Activity
            </h4>
            <DocumentProcessingTimeline events={d.processing_events} />
          </Card>
        </div>

        {/* Main Section: Comparison (Original vs Extracted) */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="p-4 flex flex-col">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <span className="bg-muted px-2 py-0.5 rounded text-xs font-mono">1</span>
              Original document
            </h4>
            <DocumentPreview documentId={d.id} mimeType={d.mime_type} />
          </Card>

          <Card className="p-4 flex flex-col h-[585px]">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <span className="bg-muted px-2 py-0.5 rounded text-xs font-mono">2</span>
              Extracted text ({d.page_count || 0} pages)
            </h4>
            <div className="flex-1 bg-muted/30 border rounded-md p-4 overflow-y-auto relative">
              {pagesLoading ? (
                <div className="flex h-full items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : allPagesText ? (
                <TypewriterText
                  text={allPagesText}
                  speed={8}
                  className="text-sm text-foreground/90 font-mono leading-relaxed"
                  autoScroll={true}
                />
              ) : d.status !== "indexed" ? (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Document is not indexed yet. Status: {d.status}
                </div>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  No page data available
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground shrink-0">{k}</span>
      <span className="font-medium text-right truncate" title={v}>
        {v}
      </span>
    </div>
  );
}
