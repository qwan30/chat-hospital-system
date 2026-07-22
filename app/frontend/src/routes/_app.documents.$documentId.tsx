import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDocument, getDocumentPage, retryIndex } from "@/lib/api/documents";
import { Loader2 } from "lucide-react";
import { ErrorState } from "@/components/hms/ErrorState";
import { DocumentPreview } from "@/components/hms/DocumentPreview";
import { DocumentProcessingTimeline } from "@/components/hms/DocumentProcessingTimeline";

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

  const { data: pageData, isLoading: pageLoading } = useQuery({
    queryKey: ["document-page", documentId, 1],
    queryFn: () => getDocumentPage(documentId, 1),
    enabled: !!d && d.status === "indexed",
  });

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
          <Button
            variant="outline"
            onClick={() => retryMutation.mutate()}
            disabled={retryMutation.isPending}
          >
            {retryMutation.isPending ? "Retrying..." : "Retry Indexing"}
          </Button>
        }
      />
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-2 p-5">
          <h4 className="text-sm font-semibold mb-2">Original document</h4>
          <DocumentPreview documentId={d.id} mimeType={d.mime_type} />
        </Card>
        <Card className="p-5 space-y-3 text-sm">
          <Row k="Uploaded" v={new Date(d.created_at).toLocaleString()} />
          <Row k="By" v={d.uploaded_by.substring(0, 8)} />
          <Row k="Patient" v={d.patient_id.substring(0, 8)} />
          <Row k="Type" v={d.mime_type} />
          {d.ocr_error && <Row k="OCR Error" v={d.ocr_error} />}
          {pageData?.ocr_confidence !== undefined && pageData?.ocr_confidence !== null && (
            <Row k="OCR Confidence (Pg 1)" v={`${Math.round(pageData.ocr_confidence * 100)}%`} />
          )}
        </Card>
        <Card className="md:col-span-2 p-5">
          <h4 className="text-sm font-semibold mb-2">Extracted text (preview Page 1)</h4>
          {pageLoading ? (
            <div className="flex justify-center p-4">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : pageData ? (
            <pre className="whitespace-pre-wrap text-xs text-muted-foreground">
              {pageData.ocr_text || "No OCR text extracted"}
            </pre>
          ) : d.status !== "indexed" ? (
            <div className="text-xs text-muted-foreground">
              Document is not indexed yet. Status: {d.status}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">No page data available</div>
          )}
        </Card>
        <Card className="p-5">
          <h4 className="mb-3 text-sm font-semibold">Processing activity</h4>
          <DocumentProcessingTimeline events={d.processing_events} />
        </Card>
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
