import { createFileRoute, Link } from "@tanstack/react-router";
import { z } from "zod";
import { AppShell } from "@/components/shell/AppShell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  ChevronLeft,
  FileText,
  AlertTriangle,
  Shield,
  ShieldAlert,
  Database,
  Hash,
  Clock,
  Sparkles,
  ExternalLink,
} from "lucide-react";

const citationSearchSchema = z.object({
  state: z.string().optional(),
});

export const Route = createFileRoute("/_app/citations/$citationId")({
  validateSearch: citationSearchSchema,
  head: ({ params }) => ({
    meta: [
      { title: `Citation ${params.citationId} — HMS AI Copilot` },
      { name: "description", content: "Detailed view of the source evidence chunk." },
    ],
  }),
  component: CitationDetails,
});

function CitationDetails() {
  const { citationId } = Route.useParams();
  const { state } = Route.useSearch();

  // Mock citation data matching typical retrieval scenarios
  const citationData = {
    id: citationId,
    title: "ACC/AHA Atrial Fibrillation Guideline 2024",
    section: "Section 5.2 — Anticoagulation Recommendation",
    author: "American College of Cardiology / American Heart Association",
    publishDate: "January 2024",
    indexedAt: "June 12, 2026, 14:32 UTC",
    method: "Hybrid (BM25 + Vector)",
    relevance: 94,
    hash: "6e3b8b093412a8740c4973a811c75c82bcff9c882bc87dfd99723fa8c9e01102",
    snippet: `For patients with non-valvular atrial fibrillation and a CHA₂DS₂-VASc score of 2 or greater in men or 3 or greater in women, oral anticoagulants (OACs) are recommended (Class 1, Level of Evidence: A). Direct oral anticoagulants (DOACs) are recommended in preference to warfarin (Class 1, Level of Evidence: A) for their superior safety profile and lower incidence of intracranial hemorrhage. Dose adjustments should be performed in accordance with renal clearance guidelines (apixaban 2.5mg BID if any two: Age >= 80, Weight <= 60kg, Creatinine >= 1.5mg/dL).`,
    sourceFile: "acc_aha_af_guidelines_2024.pdf",
  };

  const isMissing = state === "missing";
  const hasIntegrityWarning = state === "integrity-warning";

  return (
    <AppShell>
      <div className="flex flex-col gap-6">
        {/* Navigation */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" asChild className="gap-1 cursor-pointer">
            <Link to="/chat">
              <ChevronLeft className="h-4 w-4" />
              Back to Chat
            </Link>
          </Button>
          <Badge variant="outline" className="font-mono">
            ID: {citationId}
          </Badge>
        </div>

        {/* Heading */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="h-6 w-6 text-ai" />
            Source Document Viewer
          </h1>
          <p className="text-sm text-muted-foreground">
            Verifiable evidence passage retrieved to ground clinical AI answers.
          </p>
        </div>

        {/* Alerts for state simulations */}
        {isMissing && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Evidence Link Broken</AlertTitle>
            <AlertDescription>
              The referenced document page or index chunk is unavailable. It may have been archived,
              moved to another department's scope, or is currently reprocessing due to an updated
              file upload.
            </AlertDescription>
          </Alert>
        )}

        {hasIntegrityWarning && (
          <Alert
            variant="destructive"
            className="border-warning/50 text-warning dark:border-warning [&>svg]:text-warning"
          >
            <ShieldAlert className="h-4 w-4" />
            <AlertTitle>Integrity Verification Warning</AlertTitle>
            <AlertDescription>
              <strong>F-SEC-004: Cryptographic hash check failed.</strong> The source file's
              contents do not match the registered hash recorded during initial indexing. The
              document may have been modified on the host filesystem post-indexing. This chunk has
              been flagged for audit review.
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content Layout */}
        <div className="grid gap-6 md:grid-cols-3">
          {/* Main Snippet Display */}
          <div className="md:col-span-2 space-y-4">
            <Card className="h-full flex flex-col">
              <CardHeader className="border-b bg-muted/20">
                <CardTitle className="text-lg font-semibold">{citationData.title}</CardTitle>
                <CardDescription className="font-medium text-primary">
                  {citationData.section}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 p-6">
                {isMissing ? (
                  <div className="flex flex-col items-center justify-center h-48 text-center text-muted-foreground border border-dashed rounded-lg p-6 bg-muted/10">
                    <AlertTriangle className="h-10 w-10 text-muted-foreground/60 mb-2" />
                    <p className="font-semibold">Content Unavailable</p>
                    <p className="text-xs max-w-sm mt-1">
                      No text snippet can be shown because the underlying chunk was not found in the
                      vector DB.
                    </p>
                  </div>
                ) : (
                  <div className="relative rounded-lg border bg-card p-5 shadow-inner">
                    <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap italic text-foreground font-medium select-all">
                      "{citationData.snippet}"
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Metadata Rail */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Evidence Metadata</CardTitle>
                <CardDescription>Grounding details and scores</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                {/* Score */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="flex items-center gap-1">
                      <Sparkles className="h-3 w-3 text-ai" /> Retrieval Confidence
                    </span>
                    <span className="text-ai">{citationData.relevance}%</span>
                  </div>
                  <Progress value={citationData.relevance} className="h-1.5 [&>div]:bg-ai" />
                </div>

                {/* Properties */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-start gap-2">
                    <Database className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div className="space-y-0.5">
                      <p className="text-xs font-medium text-muted-foreground">Retrieval Method</p>
                      <p className="font-medium">{citationData.method}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div className="space-y-0.5">
                      <p className="text-xs font-medium text-muted-foreground">Indexed On</p>
                      <p className="font-medium">{citationData.indexedAt}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <Hash className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div className="space-y-0.5 w-full">
                      <p className="text-xs font-medium text-muted-foreground">SHA-256 Hash</p>
                      <p className="font-mono text-[10px] break-all bg-muted p-1.5 rounded border border-border/50">
                        {citationData.hash}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <Shield className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div className="space-y-0.5">
                      <p className="text-xs font-medium text-muted-foreground">
                        Compliance Verification
                      </p>
                      <p className="font-medium text-success flex items-center gap-1">
                        {hasIntegrityWarning ? (
                          <span className="text-destructive font-semibold">
                            Verification Failed
                          </span>
                        ) : (
                          <>Pass (SHIELD-01)</>
                        )}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <Button variant="outline" className="w-full text-xs gap-1.5" disabled={isMissing}>
                    <ExternalLink className="h-3 w-3" /> View Original Document
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
