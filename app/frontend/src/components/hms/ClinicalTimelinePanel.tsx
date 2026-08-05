import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ConflictSeverityPill } from "./ConflictSeverityPill";
import { Clock, Calendar, GitCommit, FileText, AlertTriangle } from "lucide-react";
import type { TimelineEventProjection } from "@/lib/api/document-timeline";

export interface ExtendedTimelineEvent extends Partial<TimelineEventProjection> {
  event_id?: string | null;
  id?: string | null;
  title?: string | null;
  description?: string | null;
  timestamp?: string | null;
}

export interface ClinicalTimelinePanelProps {
  events: ExtendedTimelineEvent[];
  onSelectEvidence?: (evidenceId: string) => void;
}

export function ClinicalTimelinePanel({ events, onSelectEvidence }: ClinicalTimelinePanelProps) {
  if (!events || events.length === 0) {
    return (
      <Card className="p-5 text-center text-sm text-muted-foreground">
        No clinical timeline events found.
      </Card>
    );
  }

  return (
    <Card className="p-5 space-y-6">
      <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
        <Clock className="h-4 w-4 text-primary" aria-hidden="true" />
        Clinical Timeline &amp; Lineage
      </h3>
      <ol className="relative border-l pl-6 space-y-6">
        {events.map((ev, index) => {
          const id = ev.event_id || ev.id || `event-${index}`;
          const clinicalDate = ev.clinical_date || ev.timestamp;
          const recordedAt = ev.recorded_at || ev.timestamp;
          const eventType = ev.event_type || ev.title || "Clinical Event";
          const conflictState = ev.conflict_state || "none";
          const reviewerState = ev.reviewer_state || "unreviewed";
          const confidence = ev.confidence !== undefined ? Math.round(ev.confidence * 100) : null;
          const evidenceIds = ev.evidence_ids || [];
          const lineage = ev.supersession_lineage || [];

          return (
            <li key={id} className="relative">
              <span
                className={`absolute -left-[31px] mt-1.5 h-3.5 w-3.5 rounded-full border-2 border-background ${
                  conflictState !== "none" ? "bg-warning" : "bg-primary"
                }`}
                aria-hidden="true"
              />
              <div className="space-y-2 rounded-lg border bg-card p-3.5 shadow-sm">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-foreground capitalize">
                      {eventType}
                    </span>
                    {ev.title && ev.title !== eventType && (
                      <span className="text-sm text-muted-foreground">({ev.title})</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {confidence !== null && (
                      <Badge variant="outline" className="text-[11px]">
                        Confidence: {confidence}%
                      </Badge>
                    )}
                    <Badge
                      variant="secondary"
                      className={`text-[11px] capitalize ${
                        reviewerState === "approved"
                          ? "bg-success/10 text-success"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {reviewerState}
                    </Badge>
                    {conflictState !== "none" && (
                      <ConflictSeverityPill
                        severity={conflictState === "value_conflict" ? "high" : "moderate"}
                      />
                    )}
                  </div>
                </div>

                {ev.description && (
                  <p className="text-xs text-muted-foreground">{ev.description}</p>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-muted-foreground bg-muted/30 p-2 rounded">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-primary shrink-0" aria-hidden="true" />
                    <span>
                      <strong className="text-foreground">Clinical Date:</strong>{" "}
                      {clinicalDate ? new Date(clinicalDate).toLocaleDateString() : "Not stated"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock
                      className="h-3.5 w-3.5 text-muted-foreground shrink-0"
                      aria-hidden="true"
                    />
                    <span>
                      <strong className="text-foreground">Recorded At:</strong>{" "}
                      {recordedAt ? new Date(recordedAt).toLocaleString() : "Unknown"}
                    </span>
                  </div>
                </div>

                {conflictState !== "none" && (
                  <div className="flex items-center gap-1.5 text-xs text-warning bg-warning/5 border border-warning/30 px-2.5 py-1.5 rounded">
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                    <span>
                      Conflict detected:{" "}
                      <strong className="capitalize">{conflictState.replace("_", " ")}</strong>
                    </span>
                  </div>
                )}

                {lineage.length > 0 && (
                  <div className="space-y-1 pt-1 border-t text-xs">
                    <div className="flex items-center gap-1 font-medium text-muted-foreground">
                      <GitCommit className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>Supersession Lineage:</span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap font-mono text-[11px]">
                      {lineage.map((rev, idx) => (
                        <span key={rev} className="bg-muted px-1.5 py-0.5 rounded border">
                          {rev}
                          {idx < lineage.length - 1 && (
                            <span className="ml-1 text-muted-foreground">→</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {evidenceIds.length > 0 && (
                  <div className="pt-2 border-t flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                      <FileText className="h-3.5 w-3.5" aria-hidden="true" /> Evidence:
                    </span>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {evidenceIds.map((eid, idx) => (
                        <button
                          key={eid}
                          type="button"
                          aria-label={`View evidence ${eid}`}
                          onClick={() => onSelectEvidence?.(eid)}
                          className="inline-flex h-6 items-center justify-center rounded-md border border-citation/30 bg-citation/10 px-2 font-mono text-xs font-semibold text-citation transition hover:bg-citation/20 cursor-pointer"
                        >
                          [{idx + 1}] {eid}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </Card>
  );
}
