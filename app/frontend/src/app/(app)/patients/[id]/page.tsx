"use client";

import { useEffect, useState, use } from "react";
import { useAuth } from "@/lib/auth-context";
import { getPatientOverview } from "@/lib/api/patients";
import type { PatientOverview } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { DetailHeader } from "@/components/patient/DetailHeader";
import { MetadataGrid, patientToMetadataFields } from "@/components/patient/MetadataGrid";
import { AISummaryCard } from "@/components/patient/AISummaryCard";
import { MiniLabStrip } from "@/components/patient/MiniLabStrip";
import { MedicationList } from "@/components/patient/MedicationList";
import { AllergyAlertsCard } from "@/components/patient/AllergyAlertsCard";
import { EncounterTimeline } from "@/components/patient/EncounterTimeline";
import { Activity, FileText, Clock, AlertTriangle } from "lucide-react";

const SAMPLE_LABS = [
  { label: "WBC", value: "7.2", unit: "K/uL", trend: "stable" as const, status: "normal" as const, referenceRange: "4.5-11.0" },
  { label: "Hgb", value: "13.8", unit: "g/dL", trend: "stable" as const, status: "normal" as const, referenceRange: "12.0-16.0" },
];

const SAMPLE_ENCOUNTERS = [
  { id: "1", date: "May 12, 2025", type: "admission", title: "Hospital Admission", description: "Admitted via ED with chest pain", status: "completed" },
  { id: "2", date: "May 13, 2025", type: "lab", title: "Cardiac Panel", description: "Troponin ordered", status: "completed" },
];

export default function PatientOverviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { apiUrl, token } = useAuth();
  const [patient, setPatient] = useState<PatientOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    getPatientOverview({ apiUrl, token }, id)
      .then((p) => { setPatient(p); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [apiUrl, token, id]);

  if (loading) return <div className="p-6 space-y-6"><Skeleton className="h-16 w-full rounded-xl" /><Skeleton className="h-[100px] w-full rounded-xl" /></div>;

  if (error) return <div className="p-6"><Card className="border-danger-100 bg-danger-50"><CardContent className="py-8 text-center"><AlertTriangle className="w-10 h-10 text-danger-400 mx-auto mb-3" /><p className="text-danger-600 text-body-strong">Unable to load patient</p><p className="text-caption text-text-muted mt-1">{error}</p></CardContent></Card></div>;

  if (!patient) return null;

  return (
    <div className="p-6 space-y-6">
      <DetailHeader fullName={patient.full_name} mrn={patient.mrn} dob={patient.dob} gender={patient.gender} status={patient.admission_status} department={patient.department} attendingPhysician={patient.attending_physician} />
      <MetadataGrid fields={patientToMetadataFields(patient)} />
      <div className="flex items-center gap-4 overflow-x-auto"><MiniLabStrip labs={SAMPLE_LABS} /></div>
      <Tabs defaultValue="summary"><TabsList><TabsTrigger value="summary"><FileText className="w-3.5 h-3.5 mr-1.5" />AI Summary</TabsTrigger><TabsTrigger value="medications"><Activity className="w-3.5 h-3.5 mr-1.5" />Medications</TabsTrigger><TabsTrigger value="encounters"><Clock className="w-3.5 h-3.5 mr-1.5" />Encounters</TabsTrigger></TabsList>
        <TabsContent value="summary" className="mt-4"><div className="grid grid-cols-3 gap-4"><div className="col-span-2 space-y-4"><AISummaryCard sections={[{ title: "Chief Complaint", content: patient.ai_summary || "No AI summary available yet.", citations: [1, 2] }]} confidence="high" citations={[{ id: 1, documentTitle: "Admission Note", page: 2 }, { id: 2, documentTitle: "Cardiology Consult", page: 1 }]} /><Card><CardHeader><CardTitle className="text-h4">Lab Trends</CardTitle></CardHeader><CardContent><MiniLabStrip labs={SAMPLE_LABS} /></CardContent></Card></div><div className="space-y-4"><AllergyAlertsCard allergies={[{ id: "1", allergen: "Penicillin", severity: "high", reaction: "Anaphylaxis", recordedDate: "Jan 2019" }, { id: "2", allergen: "Sulfa Drugs", severity: "medium", reaction: "Rash", recordedDate: "Mar 2020" }]} /><Card><CardHeader><CardTitle className="text-h4">Encounters</CardTitle></CardHeader><CardContent><EncounterTimeline encounters={SAMPLE_ENCOUNTERS} /></CardContent></Card></div></div></TabsContent>
        <TabsContent value="medications" className="mt-4"><div className="grid grid-cols-3 gap-4"><div className="col-span-2"><MedicationList medications={[{ id: "1", name: "Lisinopril", dosage: "10mg", frequency: "Once daily", route: "PO", indication: "Hypertension", startDate: "Apr 2025", status: "active", citationId: 1 }, { id: "2", name: "Metformin", dosage: "500mg", frequency: "Twice daily", route: "PO", indication: "Diabetes", startDate: "Mar 2025", status: "active" }]} /></div><div className="space-y-4"><AllergyAlertsCard allergies={[{ id: "1", allergen: "Penicillin", severity: "high", reaction: "Anaphylaxis", recordedDate: "Jan 2019" }]} /></div></div></TabsContent>
        <TabsContent value="encounters" className="mt-4"><Card><CardHeader><CardTitle className="text-h4">Encounter Timeline</CardTitle></CardHeader><CardContent><EncounterTimeline encounters={SAMPLE_ENCOUNTERS} /></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  );
}
