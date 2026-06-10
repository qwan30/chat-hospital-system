"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { UploadDropzone } from "@/components/document/UploadDropzone";
import { OCRPipelineStepper } from "@/components/document/OCRPipelineStepper";
import { Upload, FileText, CheckCircle, X, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface UploadFile { name: string; size: string; progress: number; status: "uploading" | "processing" | "done" | "error"; }

export default function BatchUploadPage() {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleFiles = (fileList: FileList) => {
    const newFiles: UploadFile[] = Array.from(fileList).map((f) => ({ name: f.name, size: (f.size / 1024 / 1024).toFixed(1) + " MB", progress: 0, status: "uploading" as const }));
    setFiles((prev) => [...prev, ...newFiles]);
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
                  {f.status === "done" && <CheckCircle className="w-4 h-4 text-success-500 flex-shrink-0" />}
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <Button variant="outline" onClick={() => setFiles([])}>Clear</Button>
              <Button disabled={uploading}><Upload className="w-4 h-4 mr-2" />Start Upload</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
