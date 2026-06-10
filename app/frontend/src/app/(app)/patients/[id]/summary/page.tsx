"use client";

import { useEffect, useState, use } from "react";
import { useAuth } from "@/lib/auth-context";
import { generateAISummary, getPatientOverview } from "@/lib/api/patients";
import type { AISummaryResponse } from "@/lib/api/patients";
import type { PatientOverview } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ContextChip } from "@/components/patient/ContextChip";
import { AISummaryCard } from "@/components/patient/AISummaryCard";
import { Sparkles, RefreshCw, AlertTriangle } from "lucide-react";

export default function PatientSummaryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { apiUrl, token } = useAuth();
  const [patient, setPatient] = useState<PatientOverview | null>(null);
  const [summary, setSummary] = useState<AISummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    getPatientOverview({ apiUrl, token }, id)
      .then((p) => { setPatient(p); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [apiUrl, token, id]);

  const handleGenerate = () => {
    if (!apiUrl || !token) return;
    setGenerating(true);
    setError("");
    generateAISummary({ apiUrl, token }, id)
      .then((s) => { setSummary(s); setGenerating(false); })
      .catch((e) => { setError(e.message); setGenerating(false); });
  };

  if (loading) {
    return <div className="p-6 space-y-6"><Skeleton className="h-10 w-48" /><Skeleton className="h-[300px] w-full rounded-xl" /></div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-primary-500" />
          <h1 className="text-h1 text-text-strong">AI Summary</h1>
        </div>
        {patient && <ContextChip fullName={patient.full_name} mrn={patient.mrn} size="sm" />}
      </div>

      {error && (
        <Card className="border-danger-100 bg-danger-50">
          <CardContent className="py-6 text-center">
            <AlertTriangle className="w-8 h-8 text-danger-400 mx-auto mb-2" />
            <p className="text-danger-600 text-body-strong">Summary generation failed</p>
            <p className="text-caption text-text-muted mt-1">{error}</p>
            <Button variant="outline" className="mt-3" onClick={handleGenerate}>
              <RefreshCw className="w-4 h-4 mr-2" />Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {!summary && !generating && !error && (
        <Card>
          <CardContent className="py-12 text-center">
            <Sparkles className="w-12 h-12 text-primary-300 mx-auto mb-4" />
            <h2 className="text-h3 text-text-strong mb-2">Generate AI Clinical Summary</h2>
            <p className="text-body text-text-muted max-w-lg mx-auto mb-6">
              Our AI will analyze patient records across all indexed documents to produce a structured clinical summary with citations.
            </p>
            <Button onClick={handleGenerate} className="gap-2">
              <Sparkles className="w-4 h-4" />Generate Summary
            </Button>
          </CardContent>
        </Card>
      )}

      {generating && <AISummaryCard sections={[]} confidence="high" loading />}

      {summary && !generating && (
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 space-y-4">
            <AISummaryCard
              sections={summary.sections.map((s) => ({ title: s.title, content: s.content, citations: s.citations }))}
              confidence={summary.confidence as "high" | "medium" | "low"}
              citations={summary.citations.map((c) => ({ id: c.id, documentTitle: c.document_title, page: c.page }))}
            />
            <Button variant="outline" onClick={handleGenerate} className="gap-2" disabled={generating}>
              <RefreshCw className="w-4 h-4" />Regenerate Summary
            </Button>
          </div>
          <div className="space-y-4">
            <Card>
              <CardContent className="p-4">
                <h4 className="text-h4 text-text-strong mb-2">Sources Used</h4>
                <div className="space-y-2">
                  {summary.citations.map((c) => (
                    <div key={c.id} className="flex items-center justify-between py-2 border-b border-border-subtle last:border-0">
                      <div>
                        <p className="text-[13px] font-medium text-text-default">{c.document_title}</p>
                        <p className="text-[11px] text-text-subtle">Page {c.page}</p>
                      </div>
                      <span className="text-[12px] font-semibold text-success-600">{Math.round(c.confidence * 100)}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
