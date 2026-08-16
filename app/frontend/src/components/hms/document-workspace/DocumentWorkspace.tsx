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
import { useEffect, useState } from "react";
import { WorkspaceToolbar } from "./WorkspaceToolbar";
import { RevisionSelector } from "./RevisionSelector";
import { PageNavigator } from "./PageNavigator";
import { OcrEditor } from "./OcrEditor";
import { Button } from "@/components/ui/button";
import { DocumentPreview } from "../DocumentPreview";
import { GeometryOverlay, BoundingBox } from "./GeometryOverlay";
import { RevisionDiff } from "./RevisionDiff";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { OcrConfidenceBadge } from "../OcrConfidenceBadge";
import { Badge } from "@/components/ui/badge";
import { Edit3 } from "lucide-react";

interface DocumentWorkspaceProps {
  documentId: string;
  selectedRevisionId?: string | null;
  onSelectRevision?: (id: string | null) => void;
}

export function DocumentWorkspace({
  documentId,
  selectedRevisionId: externalSelectedRevisionId,
  onSelectRevision: externalOnSelectRevision,
}: DocumentWorkspaceProps) {
  const queryClient = useQueryClient();
  const documentQuery = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
  });
  const revisionsQuery = useQuery({
    queryKey: ["document-revision-sets", documentId],
    queryFn: () => listRevisionSets(documentId),
  });

  const [internalSelectedRevisionId, setInternalSelectedRevisionId] = useState<string | null>(null);
  const selectedRevisionId =
    externalSelectedRevisionId !== undefined
      ? externalSelectedRevisionId
      : internalSelectedRevisionId;

  const setSelectedRevisionId = (id: string | null) => {
    setInternalSelectedRevisionId(id);
    externalOnSelectRevision?.(id);
  };

  useEffect(() => {
    if (selectedRevisionId) return;
    const submittedRevision = revisionsQuery.data?.find(
      (revision) => revision.status === "submitted",
    );
    if (submittedRevision) {
      setSelectedRevisionId(submittedRevision.revision_set_id);
    }
  }, [revisionsQuery.data, selectedRevisionId]);

  const [selectedPage, setSelectedPage] = useState(1);
  const [currentLockVersion, setCurrentLockVersion] = useState<number | undefined>();
  const [isDraftSaving, setIsDraftSaving] = useState(false);

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

  useEffect(() => {
    setCurrentLockVersion(undefined);
    setIsDraftSaving(false);
  }, [selectedPage, selectedRevisionId]);

  useEffect(() => {
    if (revisionPageQuery.data?.lock_version !== undefined) {
      setCurrentLockVersion(revisionPageQuery.data.lock_version);
    }
  }, [revisionPageQuery.data?.lock_version, revisionPageQuery.data?.page_revision_id]);

  const restoreMutation = useMutation({
    mutationFn: () => {
      const revSetId = selectedRevisionId || revisionsQuery.data?.[0]?.revision_set_id;
      if (!revSetId) return Promise.reject(new Error("No revision available to restore"));
      const pageRevId = revisionPageQuery.data?.page_revision_id || revSetId;
      return restoreRevision(
        documentId,
        revSetId,
        { revision_id: pageRevId },
        { idempotencyKey: crypto.randomUUID() },
      );
    },
    onSuccess: () => {
      toast.success("New draft created. You can now edit and submit again.");
      queryClient.invalidateQueries({ queryKey: ["document-revision-sets", documentId] });
      queryClient.invalidateQueries({ queryKey: ["document-page", documentId, selectedPage] });
      queryClient.invalidateQueries({
        queryKey: ["document-revision-page", documentId, null, selectedPage],
      });
      setSelectedRevisionId(null);
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to create new draft");
    },
  });

  const submitMutation = useMutation({
    mutationFn: () => {
      if (currentLockVersion === undefined) {
        return Promise.reject(new Error("Draft lock version is not loaded"));
      }
      return submitDraft(documentId, {
        idempotencyKey: crypto.randomUUID(),
        lockVersion: currentLockVersion,
      });
    },
    onSuccess: (res) => {
      toast.success("Draft submitted successfully! You can approve it or continue editing.");
      queryClient.invalidateQueries({ queryKey: ["document-revision-sets", documentId] });
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
      setSelectedRevisionId(res.revision_set_id);
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to submit draft");
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
      toast.success("Revision approved. Indexing generation started.");
      queryClient.invalidateQueries({ queryKey: ["document-revision-sets", documentId] });
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed to approve revision");
    },
  });

  const isHistorical =
    selectedRevisionId &&
    selectedRevisionId !== "draft" &&
    !revisionsQuery.data?.find(
      (r) => r.revision_set_id === selectedRevisionId && r.status === "draft",
    );

  const revision = revisionsQuery.data?.find((r) => r.revision_set_id === selectedRevisionId) || {
    revision_set_id: selectedRevisionId || "draft",
    revision_number: 1,
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
        <div className="flex flex-wrap items-center gap-2">
          {confidence !== undefined && confidence !== null && (
            <OcrConfidenceBadge confidence={confidence} />
          )}
          <Badge variant="outline" className="rounded-lg text-xs font-normal">
            Engine: Default
          </Badge>
          <RevisionSelector
            revisions={revisionsQuery.data || []}
            selected={selectedRevisionId}
            onSelect={(id) => setSelectedRevisionId(id || null)}
          />
          <PageNavigator page={selectedPage} onPageChange={setSelectedPage} />
        </div>

        <div className="flex items-center gap-2">
          {isHistorical ? (
            <Button
              size="sm"
              variant="default"
              className="rounded-lg h-8 gap-1.5 shadow-sm font-medium"
              onClick={() => restoreMutation.mutate()}
              disabled={restoreMutation.isPending}
            >
              <Edit3 className="h-3.5 w-3.5" />
              {restoreMutation.isPending ? "Restoring..." : "Restore as new revision"}
            </Button>
          ) : (
            <Button
              size="sm"
              className="rounded-lg h-8 px-3.5 shadow-sm font-medium"
              onClick={() => submitMutation.mutate()}
              disabled={
                submitMutation.isPending || isDraftSaving || currentLockVersion === undefined
              }
            >
              {submitMutation.isPending ? "Submitting..." : "Submit Draft"}
            </Button>
          )}

          {revision?.status === "submitted" && (
            <Button
              size="sm"
              variant="outline"
              className="rounded-lg h-8 text-emerald-600 border-emerald-500/30 hover:bg-emerald-500/10 font-medium"
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? "Approving..." : "Approve"}
            </Button>
          )}
        </div>
      </WorkspaceToolbar>

      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-2 gap-3.5 p-3 bg-muted/10 overflow-hidden">
        <div className="h-full border border-border/70 rounded-xl bg-card p-3 flex flex-col min-h-0 overflow-hidden shadow-sm">
          {documentQuery.data && (
            <DocumentPreview documentId={documentId} mimeType={documentQuery.data.mime_type}>
              <GeometryOverlay boxes={exactBoxes} staleCount={staleCount} />
            </DocumentPreview>
          )}
        </div>

        <div className="h-full border border-border/70 rounded-xl bg-card p-3 flex flex-col min-h-0 overflow-hidden shadow-sm">
          <Tabs defaultValue="corrected" className="flex-1 flex flex-col h-full min-h-0">
            <div className="flex items-center justify-between mb-2">
              <TabsList className="rounded-lg p-1 bg-muted/40 w-fit h-8">
                <TabsTrigger value="corrected" className="rounded-md text-xs font-medium px-3 h-6">
                  Corrected
                </TabsTrigger>
                <TabsTrigger value="raw" className="rounded-md text-xs font-medium px-3 h-6">
                  Raw OCR
                </TabsTrigger>
                <TabsTrigger value="diff" className="rounded-md text-xs font-medium px-3 h-6">
                  Diff
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent
              value="corrected"
              className="flex-1 flex flex-col mt-0 h-full min-h-0 overflow-hidden"
            >
              {isHistorical ? (
                <div className="flex-1 flex flex-col gap-3 min-h-0">
                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-muted/30 border text-xs">
                    <div>
                      <span className="font-semibold text-foreground">
                        Revision #{revision?.revision_number || 1}
                      </span>
                      <span className="text-muted-foreground ml-2 capitalize">
                        ({revision?.status || "historical"}) · Read-only snapshot
                      </span>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs rounded-lg gap-1.5"
                      onClick={() => restoreMutation.mutate()}
                      disabled={restoreMutation.isPending}
                    >
                      <Edit3 className="h-3 w-3" />
                      {restoreMutation.isPending ? "Restoring..." : "Edit as New Draft"}
                    </Button>
                  </div>
                  <div className="flex-1 p-4 border border-input/80 rounded-xl bg-muted/20 overflow-auto whitespace-pre-wrap font-mono text-xs sm:text-sm leading-relaxed shadow-inner min-h-0">
                    {correctedText}
                  </div>
                </div>
              ) : (
                <OcrEditor
                  documentId={documentId}
                  page={selectedPage}
                  revision={revision}
                  initialText={originalText}
                  lockVersion={currentLockVersion}
                  parentRevisionId={revisionPageQuery.data?.page_revision_id}
                  onCompare={handleCompare}
                  onLockVersionChange={setCurrentLockVersion}
                  onSavingChange={setIsDraftSaving}
                  onSaved={(savedPage) => {
                    queryClient.setQueryData(
                      ["document-revision-page", documentId, selectedRevisionId, selectedPage],
                      savedPage,
                    );
                  }}
                />
              )}
            </TabsContent>
            <TabsContent value="raw" className="flex-1 flex flex-col mt-0 h-full min-h-0 overflow-hidden">
              <div className="flex-1 p-4 border border-input/80 rounded-xl bg-muted/20 overflow-auto whitespace-pre-wrap font-mono text-xs sm:text-sm leading-relaxed shadow-inner min-h-0">
                {originalText}
              </div>
            </TabsContent>
            <TabsContent value="diff" className="flex-1 flex flex-col mt-0 h-full min-h-0 overflow-hidden">
              <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
                <RevisionDiff originalText={originalText} correctedText={correctedText} />
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
