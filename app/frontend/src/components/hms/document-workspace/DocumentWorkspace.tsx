import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDocument, getDocumentPage, getDocumentFacts } from "@/lib/api/documents";
import {
  listRevisionSets,
  restoreRevision,
  submitDraft,
  approveRevisionSet,
  getDraftPage,
  getRevisionPage,
} from "@/lib/api/document-revisions";
import { useEffect, useState, useRef } from "react";
import { WorkspaceToolbar } from "./WorkspaceToolbar";
import { RevisionSelector } from "./RevisionSelector";
import { PageNavigator } from "./PageNavigator";
import { OcrEditor } from "./OcrEditor";
import { Button } from "@/components/ui/button";
import { RevisionHistoryDrawer } from "./RevisionHistoryDrawer";
import { DocumentPreview } from "../DocumentPreview";
import { GeometryOverlay, BoundingBox } from "./GeometryOverlay";
import { RevisionDiff } from "./RevisionDiff";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { OcrConfidenceBadge } from "../OcrConfidenceBadge";
import { Badge } from "@/components/ui/badge";

export function DocumentWorkspace({ documentId }: { documentId: string }) {
  const queryClient = useQueryClient();
  const documentQuery = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
  });
  const revisionsQuery = useQuery({
    queryKey: ["document-revision-sets", documentId],
    queryFn: () => listRevisionSets(documentId),
  });

  const [selectedRevisionId, setSelectedRevisionId] = useState<string | null>(null);
  const [selectedPage, setSelectedPage] = useState(1);

  useEffect(() => {
    if (selectedRevisionId) return;
    const submittedRevision = revisionsQuery.data?.find(
      (revision) => revision.status === "submitted",
    );
    if (submittedRevision) {
      setSelectedRevisionId(submittedRevision.revision_set_id);
    }
  }, [revisionsQuery.data, selectedRevisionId]);

  const pageQuery = useQuery({
    queryKey: ["document-page", documentId, selectedPage],
    queryFn: () => getDocumentPage(documentId, selectedPage),
  });

  const factsQuery = useQuery({
    queryKey: ["document-facts", documentId],
    queryFn: () => getDocumentFacts(documentId),
  });

  const revisionPageQuery = useQuery({
    queryKey: ["document-revision-page", documentId, selectedRevisionId, selectedPage],
    queryFn: async () => {
      if (selectedRevisionId === "draft" || !selectedRevisionId) {
        return getDraftPage(documentId, selectedPage);
      }
      return getRevisionPage(documentId, selectedRevisionId, selectedPage);
    },
    retry: false,
  });

  const restoreMutation = useMutation({
    mutationFn: () => {
      if (!selectedRevisionId) return Promise.reject(new Error("No revision"));
      return restoreRevision(
        documentId,
        selectedRevisionId,
        { revision_id: selectedRevisionId },
        { idempotencyKey: crypto.randomUUID() },
      );
    },
    onSuccess: () => {
      toast.success("Revision restored");
      queryClient.invalidateQueries({ queryKey: ["document-revision-sets", documentId] });
      setSelectedRevisionId(null);
    },
  });

  const submitMutation = useMutation({
    mutationFn: () => submitDraft(documentId, { idempotencyKey: crypto.randomUUID() }),
    onSuccess: (res) => {
      toast.success("Draft submitted successfully");
      queryClient.invalidateQueries({ queryKey: ["document-revision-sets", documentId] });
      setSelectedRevisionId(res.revision_set_id);
    },
  });

  const approveMutation = useMutation({
    mutationFn: () => {
      if (!selectedRevisionId) return Promise.reject(new Error("No revision to approve"));
      return approveRevisionSet(
        documentId,
        selectedRevisionId,
        {},
        { idempotencyKey: crypto.randomUUID() },
      );
    },
    onSuccess: () => {
      toast.success("Revision approved. Generation started.");
      queryClient.invalidateQueries({ queryKey: ["document-revision-sets", documentId] });
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
    },
  });

  const isHistorical =
    selectedRevisionId &&
    selectedRevisionId !== "draft" &&
    !revisionsQuery.data?.find(
      (r) => r.revision_set_id === selectedRevisionId && r.status === "draft",
    );

  const revision = revisionsQuery.data?.find((r) => r.revision_set_id === selectedRevisionId) || {
    id: selectedRevisionId,
    status: "draft",
  };

  // Calculate geometry from facts
  const geometry: BoundingBox[] =
    factsQuery.data?.facts
      .filter((f) => f.source_page === selectedPage && f.bounding_box)
      .map((f) => ({
        id: f.id,
        ...f.bounding_box!,
        alignment_status: f.status === "aligned" ? "aligned" : "stale",
      })) || [];

  const exactBoxes = geometry.filter((item) => item.alignment_status === "aligned");
  const staleCount = geometry.length - exactBoxes.length;

  const originalText = pageQuery.data?.ocr_text || "";
  const correctedText = revisionPageQuery.data?.text || originalText;
  const confidence = pageQuery.data?.ocr_confidence;

  const handleCompare = () => {
    queryClient.invalidateQueries({ queryKey: ["document-page", documentId, selectedPage] });
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <WorkspaceToolbar>
        <RevisionHistoryDrawer
          revisions={revisionsQuery.data || []}
          selectedId={selectedRevisionId}
          onSelect={setSelectedRevisionId}
        />
        <div className="ml-auto flex items-center gap-2">
          {confidence !== undefined && confidence !== null && (
            <OcrConfidenceBadge confidence={confidence} />
          )}
          <Badge variant="outline">Engine: Default</Badge>
          <RevisionSelector
            revisions={revisionsQuery.data || []}
            selected={selectedRevisionId}
            onSelect={setSelectedRevisionId}
          />
          <PageNavigator page={selectedPage} onPageChange={setSelectedPage} />

          {!isHistorical && (
            <Button
              size="sm"
              onClick={() => submitMutation.mutate()}
              disabled={submitMutation.isPending}
            >
              Submit Draft
            </Button>
          )}
          {revision?.status === "submitted" && (
            <Button
              size="sm"
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
            >
              Approve
            </Button>
          )}
        </div>
      </WorkspaceToolbar>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 overflow-hidden p-4 bg-muted/10">
        <div className="h-full border rounded-lg bg-background p-4 flex flex-col overflow-hidden">
          {documentQuery.data && (
            <DocumentPreview documentId={documentId} mimeType={documentQuery.data.mime_type}>
              <GeometryOverlay boxes={exactBoxes} staleCount={staleCount} />
            </DocumentPreview>
          )}
        </div>

        <div className="h-full border rounded-lg bg-background p-4 flex flex-col overflow-auto">
          <Tabs defaultValue="corrected" className="flex-1 flex flex-col h-full">
            <TabsList className="mb-4">
              <TabsTrigger value="corrected">Corrected</TabsTrigger>
              <TabsTrigger value="raw">Raw OCR</TabsTrigger>
              <TabsTrigger value="diff">Diff</TabsTrigger>
            </TabsList>

            <TabsContent
              value="corrected"
              className="flex-1 flex flex-col mt-0 h-full overflow-hidden"
            >
              {isHistorical ? (
                <div className="flex-1 p-4 border rounded overflow-auto whitespace-pre-wrap font-mono text-sm">
                  {correctedText}
                </div>
              ) : (
                <OcrEditor
                  documentId={documentId}
                  page={selectedPage}
                  revision={revision}
                  initialText={originalText}
                  onCompare={handleCompare}
                />
              )}
            </TabsContent>
            <TabsContent value="raw" className="flex-1 flex flex-col mt-0 h-full overflow-hidden">
              <div className="flex-1 p-4 border rounded overflow-auto whitespace-pre-wrap font-mono text-sm">
                {originalText}
              </div>
            </TabsContent>
            <TabsContent value="diff" className="flex-1 flex flex-col mt-0 h-full overflow-hidden">
              <div className="flex-1 border rounded overflow-auto">
                <RevisionDiff originalText={originalText} correctedText={correctedText} />
              </div>
            </TabsContent>
          </Tabs>

          {isHistorical && (
            <div className="mt-4 pt-4 border-t">
              <Button onClick={() => restoreMutation.mutate()} disabled={restoreMutation.isPending}>
                {restoreMutation.isPending ? "Restoring..." : "Restore as new revision"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
