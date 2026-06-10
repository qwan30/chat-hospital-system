"use client";

import { useEffect, useState, use } from "react";
import { useAuth } from "@/lib/auth-context";
import { getMedicationReview, getPatientOverview } from "@/lib/api/patients";
import type { MedicationReviewResponse } from "@/lib/api/patients";
import type { PatientOverview } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ContextChip } from "@/components/patient/ContextChip";
import { MedicationList } from "@/components/patient/MedicationList";
import { AllergyAlertsCard } from "@/components/patient/AllergyAlertsCard";
import { Pill, RefreshCw, AlertTriangle, Sparkles, CheckCircle } from "lucide-react";

export default function MedsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { apiUrl, token } = useAuth();
  const [patient, setPatient] = useState<PatientOverview | null>(null);
  const [review, setReview] = useState<MedicationReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    getPatientOverview({ apiUrl, token }, id)
      .then((p) => { setPatient(p); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [apiUrl, token, id]);

  const handleReview = () => {
    if (!apiUrl || !token) return;
    setReviewing(true);
    setError("");
    getMedicationReview({ apiUrl, token }, id)
      .then((r) => { setReview(r); setReviewing(false); })
      .catch((e) => { setError(e.message); setReviewing(false); });
  };

  if (loading) return <div className="p-6 space-y-6"><Skeleton className="h-10 w-56" /><Skeleton className="h-[300px] w-full rounded-xl" /></div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><Pill className="w-5 h-5 text-primary-500" /><h1 className="text-h1 text-text-strong">Medication Review</h1></div>
        {patient && <ContextChip fullName={patient.full_name} mrn={patient.mrn} size="sm" />}
      </div>
      {error && <Card className="border-danger-100 bg-danger-50"><CardContent className="py-6 text-center"><AlertTriangle className="w-8 h-8 text-danger-400 mx-auto mb-2" /><p className="text-danger-600 text-body-strong">Review failed</p><p className="text-caption text-text-muted mt-1">{error}</p><Button variant="outline" className="mt-3" onClick={handleReview}><RefreshCw className="w-4 h-4 mr-2" />Retry</Button></CardContent></Card>}
      {!review && !reviewing && !error && (
        <Card><CardContent className="py-12 text-center"><Pill className="w-12 h-12 text-primary-300 mx-auto mb-4" /><h2 className="text-h3 text-text-strong mb-2">AI-Assisted Medication Review</h2><p className="text-body text-text-muted max-w-lg mx-auto mb-6">Review medications against allergies, lab results, and guidelines.</p><Button onClick={handleReview} className="gap-2"><Sparkles className="w-4 h-4" />Start Medication Review</Button></CardContent></Card>
      )}
      {reviewing && <div className="space-y-4"><Skeleton className="h-[60px] w-full rounded-xl" /><Skeleton className="h-[200px] w-full rounded-xl" /></div>}
      {review && !reviewing && (
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 space-y-4">
            <MedicationList medications={review.medications.map((m) => ({ id: m.id, name: m.name, dosage: m.dosage, frequency: m.frequency, route: m.route, indication: m.indication, startDate: m.start_date, status: m.status, citationId: m.citation_id, safetyConcern: m.safety_concern }))} />
            {review.recommendations.length > 0 && <Card><CardHeader><CardTitle className="text-h4 flex items-center gap-2"><CheckCircle className="w-4 h-4 text-success-600" />AI Recommendations</CardTitle></CardHeader><CardContent><ul className="space-y-2">{review.recommendations.map((rec, i) => <li key={i} className="flex items-start gap-2 text-[13px] text-text-default"><span className="w-5 h-5 rounded-full bg-success-50 text-success-600 flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">{i + 1}</span>{rec}</li>)}</ul></CardContent></Card>}
          </div>
          <div className="space-y-4">
            <AllergyAlertsCard allergies={review.allergies.map((a) => ({ id: a.id, allergen: a.allergen, severity: a.severity, reaction: a.reaction, recordedDate: a.recorded_date }))} />
            <Card><CardContent className="p-4"><h4 className="text-h4 text-text-strong mb-2">Review Status</h4><div className="space-y-2"><div className="flex justify-between"><span className="text-[13px] text-text-muted">Confidence</span><span className="text-[13px] font-semibold text-success-600">{review.confidence === "high" ? "High" : review.confidence === "medium" ? "Medium" : "Low"}</span></div><div className="flex justify-between"><span className="text-[13px] text-text-muted">Medications</span><span className="text-[13px] font-semibold">{review.medications.length}</span></div><div className="flex justify-between"><span className="text-[13px] text-text-muted">Allergies</span><span className="text-[13px] font-semibold">{review.allergies.length}</span></div></div></CardContent></Card>
            <Button variant="outline" onClick={handleReview} className="w-full gap-2" disabled={reviewing}><RefreshCw className="w-4 h-4" />Re-run Review</Button>
          </div>
        </div>
      )}
    </div>
  );
}
