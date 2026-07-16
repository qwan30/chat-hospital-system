import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { getPatientDocuments, type DocumentRead } from "@/lib/api/patients";

export const Route = createFileRoute("/_app/patients/$patientId/documents")({
  head: () => ({ meta: [{ title: "Documents — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { patientId } = Route.useParams();

  const {
    data: documents,
    isLoading,
    error,
  } = useQuery<DocumentRead[]>({
    queryKey: ["patient-documents", patientId],
    queryFn: () => getPatientDocuments(patientId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card className="p-0 overflow-hidden">
          <div className="animate-pulse">
            <div className="bg-muted/40 px-4 py-2">
              <div className="h-4 w-64 rounded bg-muted" />
            </div>
            {[1, 2, 3].map((i) => (
              <div key={i} className="border-t px-4 py-2">
                <div className="h-4 w-48 rounded bg-muted" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (error || !documents) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-destructive">Unable to load documents. Please try again.</p>
        </Card>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="space-y-4">
        <Card className="p-5">
          <p className="text-sm text-muted-foreground">No documents found for this patient.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-left">Document</th>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Date</th>
              <th className="px-4 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} className="border-t">
                <td className="px-4 py-2 font-medium">{doc.title}</td>
                <td className="px-4 py-2">{formatDocType(doc.document_type)}</td>
                <td className="px-4 py-2 text-xs">
                  {new Date(doc.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-2 text-xs">
                  <span
                    className={
                      doc.status === "indexed"
                        ? "text-success"
                        : doc.status === "index_failed" || doc.status === "ocr_failed"
                          ? "text-destructive"
                          : "text-muted-foreground"
                    }
                  >
                    {doc.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function formatDocType(docType: string): string {
  const labels: Record<string, string> = {
    lab_result: "Lab Result",
    clinical_note: "Clinical Note",
    discharge_summary: "Discharge Summary",
    imaging_report: "Imaging",
    prescription: "Prescription",
    encounter_note: "Encounter Note",
    hms_appointment: "Appointment",
    hms_lab_result: "Lab Result",
    hms_medical_record: "Medical Record",
    hms_allergy: "Allergy",
  };
  return labels[docType] ?? docType;
}
