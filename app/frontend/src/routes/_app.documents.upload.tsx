import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, Loader2, FileUp } from "lucide-react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api/documents";

export const Route = createFileRoute("/_app/documents/upload")({
  head: () => ({ meta: [{ title: "Upload documents — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [patientId, setPatientId] = useState("20000000-0000-0000-0000-000000000003");
  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState("clinical_note");
  const [file, setFile] = useState<File | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("Please select a file to upload.");
      if (!title) throw new Error("Please enter a document title.");
      return uploadDocument(patientId, title, documentType, file);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      navigate({ to: "/documents/$documentId", params: { documentId: data.id } });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Failed to upload document");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    uploadMutation.mutate();
  };

  return (
    <AppShell>
      <PageHeader
        title="Upload documents"
        description="Files ingest into the OCR + vector pipeline."
      />
      <div className="max-w-2xl mx-auto mt-6">
        <Card className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="patientId">Patient ID (UUID)</Label>
              <Input
                id="patientId"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="title">Document Title</Label>
              <Input
                id="title"
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

            <div className="space-y-2">
              <Label htmlFor="file">File</Label>
              <div className="flex items-center gap-4">
                <Input
                  id="file"
                  type="file"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  required
                  className="w-full cursor-pointer"
                />
              </div>
            </div>

            {errorMsg && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {errorMsg}
              </div>
            )}

            <Button type="submit" disabled={uploadMutation.isPending} className="w-full">
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Uploading...
                </>
              ) : (
                <>
                  <FileUp className="mr-2 h-4 w-4" /> Upload Document
                </>
              )}
            </Button>
          </form>
        </Card>
      </div>
    </AppShell>
  );
}
