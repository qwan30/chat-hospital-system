import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { DocumentUploadFlow } from "@/components/hms/document-upload/DocumentUploadFlow";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/_app/documents/upload")({
  head: () => ({ meta: [{ title: "Upload documents — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const [patientId, setPatientId] = useState("20000000-0000-0000-0000-000000000003");
  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState("clinical_note");

  return (
    <AppShell>
      <PageHeader
        title="Upload documents"
        description="Files ingest into the OCR + vector pipeline."
      />
      <div className="max-w-2xl mx-auto mt-6">
        <Card className="p-6">
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="patientId">Patient ID (UUID)</Label>
              <Input
                id="patientId"
                form="upload-form"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="title">Document Title</Label>
              <Input
                id="title"
                form="upload-form"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Discharge Summary"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="documentType">Document Type</Label>
              <select
                id="documentType"
                form="upload-form"
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
              >
                <option value="clinical_note">Clinical Note</option>
                <option value="scan">Scan / Image</option>
                <option value="lab_result">Lab Result</option>
                <option value="protocol">Protocol / Guideline</option>
              </select>
            </div>

            <DocumentUploadFlow patientId={patientId} title={title} documentType={documentType} />
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
