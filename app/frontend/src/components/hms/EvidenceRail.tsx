import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { FileText, ExternalLink, Eye, Tag, Layers, CheckCircle, Target } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

export interface EvidenceLabel {
  stableId: string;
  inlineNumber: number;
  display: string;
}

export function evidenceLabel(messageId: string, evidenceId: string, index: number): EvidenceLabel {
  return {
    stableId: `${messageId}:${evidenceId}`,
    inlineNumber: index + 1,
    display: `[${index + 1}]`,
  };
}

export interface BoundingBox {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  [key: string]: unknown;
}

export interface EvidenceItem {
  id: string;
  /** Stable backend evidence identity; `id` remains the compatibility alias. */
  evidence_id?: string;
  n: number;
  title: string;
  source: string;
  date: string;
  snippet: string;
  relevance: number;
  document_id: string;
  messageId?: string;
  page?: number;
  revision?: string;
  approvalState?: string;
  score?: number;
  retrievalMethod?: string;
  offsets?: string | { start?: number; end?: number };
  alignedBoundingBox?: BoundingBox | string;
  alignedGeometryStatus?: string | boolean;
  revision_set_id?: string;
  page_revision_id?: string;
  start_offset?: number;
  end_offset?: number;
  bounding_boxes?: BoundingBox[] | string;
}

export interface EvidenceRailProps {
  items: EvidenceItem[];
  selectedMessageId?: string | null;
  onSelectMessage?: (msgId: string | null) => void;
}

const SNIPPET_PREVIEW_LENGTH = 120;

export function EvidenceRail({ items, selectedMessageId }: EvidenceRailProps) {
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);

  const displayedItems = useMemo(() => {
    if (!selectedMessageId) return items;
    return items.filter((it) => !it.messageId || it.messageId === selectedMessageId);
  }, [items, selectedMessageId]);

  const buildSearch = (item: EvidenceItem): Record<string, unknown> | undefined => {
    const params: Record<string, unknown> = {};
    if (item.page !== undefined) params.page = item.page;
    if (item.revision || item.revision_set_id) {
      params.revision = item.revision ?? item.revision_set_id;
    }
    if (item.page_revision_id) params.page_revision_id = item.page_revision_id;
    if (item.start_offset !== undefined) params.start_offset = item.start_offset;
    if (item.end_offset !== undefined) params.end_offset = item.end_offset;
    if (item.offsets) params.offsets = formatOffsets(item.offsets);
    const geometryStatus = String(item.alignedGeometryStatus ?? "").toLowerCase();
    const geometryIsAligned =
      item.alignedGeometryStatus === true || geometryStatus.includes("aligned");
    if (item.alignedBoundingBox && geometryIsAligned) {
      params.bbox =
        typeof item.alignedBoundingBox === "string"
          ? item.alignedBoundingBox
          : JSON.stringify(item.alignedBoundingBox);
    }
    if (item.bounding_boxes && geometryIsAligned) {
      params.bbox =
        typeof item.bounding_boxes === "string"
          ? item.bounding_boxes
          : JSON.stringify(item.bounding_boxes);
    }
    return Object.keys(params).length > 0 ? params : undefined;
  };

  const formatOffsets = (offsets?: string | { start?: number; end?: number }): string | null => {
    if (!offsets) return null;
    if (typeof offsets === "string") return offsets;
    if (offsets.start !== undefined && offsets.end !== undefined) {
      return `${offsets.start}-${offsets.end}`;
    }
    return null;
  };

  return (
    <>
      <div className="flex h-full flex-col">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Evidence</h3>
          <Badge variant="secondary" className="bg-citation/10 text-citation">
            {displayedItems.length} citations
          </Badge>
        </div>
        <div className="space-y-3 overflow-y-auto pr-1">
          {displayedItems.map((it, index) => {
            const evidenceId = it.evidence_id ?? it.id;
            const stableKey = `${selectedMessageId || it.messageId || "default"}:${evidenceId}`;
            const label = evidenceLabel(
              selectedMessageId || it.messageId || "default",
              evidenceId,
              index,
            );
            const isLong = it.snippet.length > SNIPPET_PREVIEW_LENGTH;
            const preview = isLong
              ? it.snippet.slice(0, SNIPPET_PREVIEW_LENGTH).trimEnd() + "…"
              : it.snippet;
            const offsetsStr = formatOffsets(it.offsets);
            const scoreDisplay =
              it.score !== undefined ? Math.round(it.score * 100) : Math.round(it.relevance * 100);

            return (
              <Card key={stableKey} className="p-3">
                <div className="flex items-start gap-2">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-citation/10 font-mono text-[10px] font-semibold text-citation">
                    {selectedMessageId ? label.display : `[${it.n}]`}
                  </div>
                  <div className="min-w-0 flex-1 overflow-hidden">
                    <p className="truncate text-sm font-medium">{it.title}</p>
                    <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground flex-wrap">
                      <span className="inline-flex items-center gap-1">
                        <FileText className="h-3 w-3 shrink-0" />
                        {it.source}
                      </span>
                      <span>·</span>
                      <span>{it.date}</span>
                      {it.page !== undefined && (
                        <>
                          <span>·</span>
                          <span className="font-semibold text-foreground">Page {it.page}</span>
                        </>
                      )}
                    </p>

                    <div className="mt-2 rounded-md bg-muted/60 p-2 text-xs leading-relaxed text-muted-foreground break-words overflow-hidden">
                      &ldquo;{preview}&rdquo;
                    </div>

                    {(it.revision ||
                      it.approvalState ||
                      it.retrievalMethod ||
                      offsetsStr ||
                      it.alignedGeometryStatus) && (
                      <div className="mt-2 grid grid-cols-1 gap-1 text-[11px] text-muted-foreground bg-muted/20 p-1.5 rounded border border-border/50">
                        {it.revision && (
                          <div className="flex items-center gap-1">
                            <Layers className="h-3 w-3 text-primary shrink-0" />
                            <span>
                              Revision: <strong className="text-foreground">{it.revision}</strong>
                            </span>
                          </div>
                        )}
                        {it.approvalState && (
                          <div className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3 text-success shrink-0" />
                            <span>
                              Approval:{" "}
                              <strong className="text-foreground">{it.approvalState}</strong>
                            </span>
                          </div>
                        )}
                        {it.retrievalMethod && (
                          <div className="flex items-center gap-1">
                            <Tag className="h-3 w-3 text-info shrink-0" />
                            <span>
                              Retrieval:{" "}
                              <strong className="text-foreground">{it.retrievalMethod}</strong>
                            </span>
                          </div>
                        )}
                        {offsetsStr && (
                          <div className="flex items-center gap-1">
                            <span>
                              Offsets:{" "}
                              <span className="font-mono text-foreground">{offsetsStr}</span>
                            </span>
                          </div>
                        )}
                        {it.alignedGeometryStatus && (
                          <div className="flex items-center gap-1">
                            <Target className="h-3 w-3 text-ai shrink-0" />
                            <span>
                              Geometry:{" "}
                              <strong className="text-foreground">
                                {String(it.alignedGeometryStatus)}
                              </strong>
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="mt-2 flex items-center justify-between gap-2 flex-wrap">
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        Relevance {scoreDisplay}%
                      </span>
                      <div className="flex items-center gap-2">
                        {isLong && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs text-primary hover:text-primary/80 cursor-pointer"
                            onClick={() => setSelectedEvidence(it)}
                          >
                            <Eye className="mr-1 h-3 w-3" />
                            View Details
                          </Button>
                        )}
                        <Link
                          to="/documents/$documentId"
                          params={{ documentId: it.document_id }}
                          search={buildSearch(it) as Record<string, unknown>}
                          className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                        >
                          Open Document <ExternalLink className="h-3 w-3" />
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      <Dialog
        open={!!selectedEvidence}
        onOpenChange={(open) => {
          if (!open) setSelectedEvidence(null);
        }}
      >
        <DialogContent className="max-w-xl max-h-[80vh] overflow-y-auto">
          {selectedEvidence && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-citation/10 font-mono text-xs font-semibold text-citation">
                    [{selectedEvidence.n}]
                  </div>
                  <DialogTitle className="text-base">{selectedEvidence.title}</DialogTitle>
                </div>
                <DialogDescription className="flex items-center gap-1.5 pt-1 flex-wrap">
                  <FileText className="h-3.5 w-3.5" />
                  <span>
                    {selectedEvidence.source} · {selectedEvidence.date}
                  </span>
                  {selectedEvidence.page !== undefined && (
                    <span>· Page {selectedEvidence.page}</span>
                  )}
                </DialogDescription>
              </DialogHeader>

              <div className="rounded-lg border bg-muted/40 p-4 text-sm leading-relaxed text-foreground break-words whitespace-pre-wrap">
                &ldquo;{selectedEvidence.snippet}&rdquo;
              </div>

              {(selectedEvidence.revision ||
                selectedEvidence.approvalState ||
                selectedEvidence.retrievalMethod ||
                selectedEvidence.offsets ||
                selectedEvidence.alignedGeometryStatus) && (
                <div className="space-y-1 text-xs text-muted-foreground border-t pt-2">
                  {selectedEvidence.revision && (
                    <p>
                      <strong>Revision:</strong> {selectedEvidence.revision}
                    </p>
                  )}
                  {selectedEvidence.approvalState && (
                    <p>
                      <strong>Approval State:</strong> {selectedEvidence.approvalState}
                    </p>
                  )}
                  {selectedEvidence.retrievalMethod && (
                    <p>
                      <strong>Retrieval Method:</strong> {selectedEvidence.retrievalMethod}
                    </p>
                  )}
                  {selectedEvidence.offsets && (
                    <p>
                      <strong>Offsets:</strong>{" "}
                      {typeof selectedEvidence.offsets === "string"
                        ? selectedEvidence.offsets
                        : `${selectedEvidence.offsets.start}-${selectedEvidence.offsets.end}`}
                    </p>
                  )}
                  {selectedEvidence.alignedGeometryStatus && (
                    <p>
                      <strong>Geometry Status:</strong>{" "}
                      {String(selectedEvidence.alignedGeometryStatus)}
                    </p>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between pt-2">
                <Badge variant="secondary" className="bg-citation/10 text-citation">
                  Relevance{" "}
                  {selectedEvidence.score !== undefined
                    ? Math.round(selectedEvidence.score * 100)
                    : Math.round(selectedEvidence.relevance * 100)}
                  %
                </Badge>
                <Link
                  to="/documents/$documentId"
                  params={{
                    documentId: selectedEvidence.document_id,
                  }}
                  search={buildSearch(selectedEvidence) as Record<string, unknown>}
                  className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                >
                  Open Document <ExternalLink className="h-4 w-4" />
                </Link>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
