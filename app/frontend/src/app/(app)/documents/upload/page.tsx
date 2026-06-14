"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { UploadDropzone } from "@/components/document/UploadDropzone";
import { Upload, FileText, CheckCircle, X, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { uploadDocument } from "@/lib/api/documents";
import { useAuth } from "@/lib/auth-context";

interface UploadFile { file: File; name: string; size: string; progress: number; status: "pending" | "uploading" | "processing" | "done" | "error"; documentId?: string; }

export default function BatchUploadPage() {
  const { apiUrl, token } = useAuth();
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleFiles = (fileList: FileList) => {
    const newFiles: UploadFile[] = Array.from(fileList).map((f) => ({ file: f, name: f.name, size: (f.size / 1024 / 1024).toFixed(1) + " MB", progress: 0, status: "pending" as const }));
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const startUpload = async () => {
    setUploading(true);
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== "pending" && files[i].status !== "error") continue;

      setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: "uploading", progress: 50 } : f));
      
      const formData = new FormData();
      // Using a test synthetic patient ID for now
      formData.append("patient_id", "00000000-0000-0000-0000-000000000001");
      formData.append("title", files[i].name);
      formData.append("document_type", "Clinical Note");
      formData.append("file", files[i].file);

      try {
        if (!apiUrl || !token) throw new Error("Not authenticated");
        const res = await uploadDocument({ apiUrl, token }, formData);
        setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: "done", progress: 100, documentId: res.id } : f));
      } catch (err) {
        setFiles(prev => prev.map((f, idx) => idx === i ? { ...f, status: "error", progress: 0 } : f));
      }
    }
    setUploading(false);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/documents"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div><h1 className="text-h1 text-text-strong">Upload Documents</h1><p className="text-caption text-text-muted">Add new documents to the knowledge base</p></div>
      </div>

      <UploadDropzone onFilesSelected={handleFiles} />

      {files.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-h4">Upload Queue ({files.length} files)</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {files.map((f, i) => (
                <div key={i} className="flex items-center gap-4 p-3 bg-bg-surface-tint rounded-lg border border-border-subtle">
                  <FileText className="w-5 h-5 text-text-subtle flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[13px] font-medium text-text-default truncate">{f.name}</span>
                      <span className="text-[11px] text-text-subtle ml-2 flex-shrink-0">{f.size}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={f.progress} className="h-1.5 flex-1" />
                      <Badge variant="outline" className={f.status === "done" ? "bg-success-50 text-success-600" : f.status === "error" ? "bg-danger-50 text-danger-600" : "bg-primary-50 text-primary-600"}>{f.status}</Badge>
                    </div>
                  </div>
                  {f.status === "error" && <X className="w-4 h-4 text-danger-500 flex-shrink-0" />}
                  {f.status === "done" && f.documentId && <Link href={`/documents/${f.documentId}`}><CheckCircle className="w-4 h-4 text-success-500 flex-shrink-0 cursor-pointer hover:text-success-600" /></Link>}
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <Button variant="outline" onClick={() => setFiles([])}>Clear</Button>
              <Button disabled={uploading} onClick={startUpload}><Upload className="w-4 h-4 mr-2" />Start Upload</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
