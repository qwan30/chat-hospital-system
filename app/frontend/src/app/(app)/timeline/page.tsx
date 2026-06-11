"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { EncounterTimeline } from "@/components/patient/EncounterTimeline";
import { ProcessingTimeline } from "@/components/document/ProcessingTimeline";
import { Activity, FileText, ShieldCheck, Stethoscope, ScrollText } from "lucide-react";

const ENCOUNTERS = [
  { id: "e1", date: "Jun 10, 2026", type: "admission", title: "Hospital Admission — John Doe", description: "Admitted via ED with acute chest pain.", status: "completed" },
  { id: "e2", date: "Jun 09, 2026", type: "consult", title: "Cardiology Consult — John Doe", description: "Dr. Bob Smith evaluated. EKG normal.", status: "completed" },
  { id: "e3", date: "Jun 09, 2026", type: "lab", title: "Cardiac Panel — John Doe", description: "Troponin I: 0.02 ng/mL.", status: "completed" },
  { id: "e4", date: "Jun 08, 2026", type: "medication", title: "Medication Review — Jane Roe", description: "Lisinopril continued at 10mg daily.", status: "completed" },
  { id: "e5", date: "Jun 07, 2026", type: "procedure", title: "MRI Brain — Jane Roe", description: "No acute intracranial abnormality.", status: "completed" },
  { id: "e6", date: "Jun 06, 2026", type: "admission", title: "ED Triage — Sam Wilson", description: "Acute abdominal pain, RLQ. ESI-3.", status: "completed" },
  { id: "e7", date: "Jun 05, 2026", type: "discharge", title: "Discharge — Sam Wilson", description: "Appendicitis ruled out.", status: "completed" },
  { id: "e8", date: "Jun 10, 2026", type: "consult", title: "Follow-up — John Doe", description: "BP 138/85. Continue regimen.", status: "active" },
];

const AUDIT_EVENTS = [
  { id: "a1", timestamp: "2026-06-10 14:32", actor: "Dr. Bob Smith", action: "query_patient_data", patient: "John Doe", outcome: "allowed" },
  { id: "a2", timestamp: "2026-06-10 13:15", actor: "Dr. Bob Smith", action: "view_document", patient: "John Doe", outcome: "allowed" },
  { id: "a3", timestamp: "2026-06-10 11:48", actor: "Carol Nurse", action: "upload_document", patient: "Sam Wilson", outcome: "allowed" },
  { id: "a4", timestamp: "2026-06-10 09:22", actor: "Carol Nurse", action: "query_patient_data", patient: "Jane Roe", outcome: "denied" },
  { id: "a5", timestamp: "2026-06-09 16:05", actor: "Alice Admin", action: "export_audit_log", patient: "—", outcome: "allowed" },
  { id: "a6", timestamp: "2026-06-09 08:30", actor: "Dr. Bob Smith", action: "login", patient: "—", outcome: "allowed" },
];

const DOC_EVENTS = [
  { id: "d1", timestamp: "2026-06-10 10:15", title: "CBC Lab Report — John Doe", event: "Indexed", status: "completed" },
  { id: "d2", timestamp: "2026-06-09 15:42", title: "Cardiology Note — John Doe", event: "Indexed", status: "completed" },
  { id: "d3", timestamp: "2026-06-08 09:00", title: "MRI Report — Jane Roe", event: "OCR Completed", status: "completed" },
  { id: "d4", timestamp: "2026-06-10 08:30", title: "Triage Assessment — Sam Wilson", event: "Uploaded", status: "completed" },
  { id: "d5", timestamp: "2026-06-10 08:31", title: "Triage Assessment — Sam Wilson", event: "OCR Processing", status: "active" },
];

export default function TimelinePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-h2 text-text-strong">Timeline</h1>
        <p className="text-[14px] text-text-muted mt-1">Recent clinical, document, and audit activity across all patients.</p>
      </div>

      <Tabs defaultValue="clinical">
        <TabsList>
          <TabsTrigger value="clinical"><Stethoscope className="w-3.5 h-3.5 mr-1.5" />Clinical</TabsTrigger>
          <TabsTrigger value="documents"><ScrollText className="w-3.5 h-3.5 mr-1.5" />Documents</TabsTrigger>
          <TabsTrigger value="audit"><ShieldCheck className="w-3.5 h-3.5 mr-1.5" />Audit</TabsTrigger>
        </TabsList>

        <TabsContent value="clinical" className="mt-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-h4 flex items-center gap-2"><Activity className="w-4 h-4 text-primary-600" />Clinical Encounters</CardTitle>
            </CardHeader>
            <CardContent><EncounterTimeline encounters={ENCOUNTERS} /></CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-h4 flex items-center gap-2"><FileText className="w-4 h-4 text-primary-600" />Document Processing</CardTitle>
            </CardHeader>
            <CardContent><ProcessingTimeline /></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-h4">Recent Document Events</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {DOC_EVENTS.map((ev) => (
                  <div key={ev.id} className="flex items-start gap-3 p-3 rounded-lg bg-bg-surface-tint border border-border-subtle">
                    <div className="w-8 h-8 rounded-full bg-primary-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <FileText className="w-3.5 h-3.5 text-primary-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-semibold text-text-default">{ev.title}</span>
                        <Badge variant="outline" className={ev.status === "completed" ? "bg-success-50 text-success-600" : "bg-primary-50 text-primary-600"}>{ev.event}</Badge>
                      </div>
                      <p className="text-[12px] text-text-muted mt-0.5">{ev.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-h4 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-primary-600" />Audit Events</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative pl-8">
                <div className="absolute left-3 top-0 bottom-0 w-px bg-border-default" />
                <div className="space-y-4">
                  {AUDIT_EVENTS.map((ev) => (
                    <div key={ev.id} className="relative">
                      <span className={`absolute -left-8 w-6 h-6 rounded-full border-2 flex items-center justify-center ${ev.outcome === "allowed" ? "bg-success-50 border-success-500" : "bg-danger-50 border-danger-500"}`}>
                        <ShieldCheck className={`w-3 h-3 ${ev.outcome === "allowed" ? "text-success-600" : "text-danger-600"}`} />
                      </span>
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[13px] font-semibold text-text-default">{ev.actor}</span>
                            <Badge variant="outline" className={ev.outcome === "allowed" ? "bg-success-50 text-success-600" : "bg-danger-50 text-danger-600"}>{ev.outcome}</Badge>
                          </div>
                          <p className="text-[12px] text-text-muted">{ev.action}{ev.patient !== "—" ? " · Patient: " + ev.patient : ""}</p>
                        </div>
                        <span className="text-[11px] text-text-subtle flex-shrink-0 ml-4">{ev.timestamp}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
