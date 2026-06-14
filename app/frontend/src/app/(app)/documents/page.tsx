"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { listDocuments, type DocumentItem } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DocumentsTable } from "@/components/document/DocumentsTable";
import { UploadDropzone } from "@/components/document/UploadDropzone";
import { SemanticSearchPanel } from "@/components/document/SemanticSearchPanel";
import { StorageUsageDonut } from "@/components/document/StorageUsageDonut";
import { Search, Upload, FileText } from "lucide-react";

import { uploadDocument } from "@/lib/api/documents";
import Link from "next/link";

export default function DocumentsPage() {
  const { apiUrl, token } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDocuments = () => {
    if (!apiUrl || !token) return;
    setLoading(true);
    listDocuments({ apiUrl, token }).then((d) => { setDocuments(d); setLoading(false); }).catch((e) => { setError(e.message); setLoading(false); });
  };

  useEffect(() => {
    fetchDocuments();
  }, [apiUrl, token]);

  const handleQuickUpload = async (fileList: FileList) => {
    if (!apiUrl || !token) return;
    const files = Array.from(fileList);
    
    for (const file of files) {
      const formData = new FormData();
      formData.append("patient_id", "00000000-0000-0000-0000-000000000001");
      formData.append("title", file.name);
      formData.append("document_type", "Clinical Note");
      formData.append("file", file);
      
      try {
        await uploadDocument({ apiUrl, token }, formData);
      } catch (err) {
        console.error("Upload error:", err);
      }
    }
    fetchDocuments();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-h1 text-text-strong">Documents</h1><p className="text-caption text-text-muted mt-1">{documents.length} documents indexed</p></div>
        <Link href="/documents/upload">
          <Button className="gap-2"><Upload className="w-4 h-4" />Upload</Button>
        </Link>
      </div>

      {error && <Card className="border-danger-100 bg-danger-50"><CardContent className="py-6 text-center"><p className="text-danger-600 text-body-strong">Failed to load documents</p><p className="text-caption text-text-muted mt-1">{error}</p></CardContent></Card>}

      <div className="grid grid-cols-[minmax(0,1fr)_360px] gap-6">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" /><Input placeholder="Search documents..." className="pl-9" /></div>
          </div>
          <UploadDropzone onFilesSelected={handleQuickUpload} />
          <Card>
            <CardHeader><CardTitle className="text-h4">All Documents</CardTitle></CardHeader>
            <CardContent>
              {loading ? <div className="space-y-2">{[1,2,3,4,5].map((i) => <Skeleton key={i} className="h-[52px] w-full rounded-lg" />)}</div> : <DocumentsTable documents={documents.map((d) => ({ id: d.id, title: d.title, patientName: d.patient_id, documentType: d.document_type, status: d.status, ocrConfidence: d.ocr_confidence, pageCount: d.page_count, createdAt: d.created_at }))} />}
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <SemanticSearchPanel onSearch={(q) => console.log("Search:", q)} />
          <StorageUsageDonut usedGB={12.4} totalGB={50} />
        </div>
      </div>
    </div>
  );
}
