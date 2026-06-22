import { useState } from "react";
import { Card } from "@/components/ui/card";
import { FileText, ExternalLink, Eye } from "lucide-react";
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

export interface EvidenceItem {
  id: string;
  n: number;
  title: string;
  source: string;
  date: string;
  snippet: string;
  relevance: number;
  document_id: string;
}

/** Max characters shown inline before truncation */
const SNIPPET_PREVIEW_LENGTH = 120;

export function EvidenceRail({ items }: { items: EvidenceItem[] }) {
  const [selectedEvidence, setSelectedEvidence] =
    useState<EvidenceItem | null>(null);

  return (
    <>
      <div className="flex h-full flex-col">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Evidence</h3>
          <Badge variant="secondary" className="bg-citation/10 text-citation">
            {items.length} citations
          </Badge>
        </div>
        <div className="space-y-3 overflow-y-auto pr-1">
          {items.map((it) => {
            const isLong = it.snippet.length > SNIPPET_PREVIEW_LENGTH;
            const preview = isLong
              ? it.snippet.slice(0, SNIPPET_PREVIEW_LENGTH).trimEnd() + "…"
              : it.snippet;

            return (
              <Card key={it.id} className="p-3">
                <div className="flex items-start gap-2">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-citation/10 font-mono text-[10px] font-semibold text-citation">
                    [{it.n}]
                  </div>
                  <div className="min-w-0 flex-1 overflow-hidden">
                    <p className="truncate text-sm font-medium">{it.title}</p>
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                      <FileText className="h-3 w-3 shrink-0" />
                      {it.source} · {it.date}
                    </p>
                    {/* Snippet preview — word-wrapped, no horizontal scroll */}
                    <div className="mt-2 rounded-md bg-muted/60 p-2 text-xs leading-relaxed text-muted-foreground break-words overflow-hidden">
                      &ldquo;{preview}&rdquo;
                    </div>
                    <div className="mt-2 flex items-center justify-between gap-2 flex-wrap">
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        Relevance {(it.relevance * 100).toFixed(0)}%
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
                          className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                        >
                          Open Document{" "}
                          <ExternalLink className="h-3 w-3" />
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

      {/* Evidence Detail Popup — centered modal */}
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
                  <DialogTitle className="text-base">
                    {selectedEvidence.title}
                  </DialogTitle>
                </div>
                <DialogDescription className="flex items-center gap-1.5 pt-1">
                  <FileText className="h-3.5 w-3.5" />
                  {selectedEvidence.source} · {selectedEvidence.date}
                </DialogDescription>
              </DialogHeader>

              {/* Full snippet content */}
              <div className="rounded-lg border bg-muted/40 p-4 text-sm leading-relaxed text-foreground break-words whitespace-pre-wrap">
                &ldquo;{selectedEvidence.snippet}&rdquo;
              </div>

              {/* Meta info */}
              <div className="flex items-center justify-between pt-2">
                <Badge
                  variant="secondary"
                  className="bg-citation/10 text-citation"
                >
                  Relevance{" "}
                  {(selectedEvidence.relevance * 100).toFixed(0)}%
                </Badge>
                <Link
                  to="/documents/$documentId"
                  params={{
                    documentId: selectedEvidence.document_id,
                  }}
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
