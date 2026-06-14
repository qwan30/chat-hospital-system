"use client";

import { use, useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, ArrowLeft, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import Link from "next/link";
import { getDocument } from "@/lib/api/documents";
import { useAuth } from "@/lib/auth-context";
import { type DocumentItem } from "@/lib/api-client";

export default function DocumentPreviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { apiUrl, token } = useAuth();
  
  const [doc, setDoc] = useState<DocumentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageImageUrls, setPageImageUrls] = useState<Record<number, string>>({});

  useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    getDocument({ apiUrl, token }, id)
      .then((d) => {
        setDoc(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [id, apiUrl, token]);

  useEffect(() => {
    if (!doc || !apiUrl || !token) return;
    
    // Fetch image for current page
    if (!pageImageUrls[currentPage]) {
      fetch(`${apiUrl.replace(/\/+$/, "")}/documents/${id}/pages/${currentPage}/image`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => {
        if (!res.ok) throw new Error("Failed to load image");
        return res.blob();
      })
      .then(blob => {
        setPageImageUrls(prev => ({ ...prev, [currentPage]: URL.createObjectURL(blob) }));
      })
      .catch(err => console.error("Error loading page image:", err));
    }
    
    // Pre-fetch thumbnails for all pages (or at least let's do it for thumbnails)
    const totalPages = doc.page_count || 1;
    for (let p = 1; p <= totalPages; p++) {
      if (!pageImageUrls[p]) {
        fetch(`${apiUrl.replace(/\/+$/, "")}/documents/${id}/pages/${p}/image`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => res.ok ? res.blob() : Promise.reject())
        .then(blob => {
          setPageImageUrls(prev => ({ ...prev, [p]: URL.createObjectURL(blob) }));
        })
        .catch(() => {});
      }
    }
  }, [doc, currentPage, id, apiUrl, token]);

  if (loading) return <div className="p-6 flex justify-center"><Loader2 className="w-6 h-6 animate-spin" /></div>;
  if (error) return <div className="p-6 text-danger-500">{error}</div>;
  if (!doc) return null;

  const totalPages = doc.page_count || 1;
  const pagesArray = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/documents"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div>
          <h1 className="text-h1 text-text-strong">{doc.title}</h1>
          <p className="text-caption text-text-muted">Document ID: {id} · {totalPages} pages · {doc.status}</p>
        </div>
        {doc.ocr_confidence !== undefined && (
          <Badge variant="outline" className="bg-success-50 text-success-600 ml-2">
            OCR: {Math.round(doc.ocr_confidence * 100)}%
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-[176px_1fr] gap-4">
        <div className="space-y-2 h-[600px] overflow-y-auto pr-2">
          {pagesArray.map((p) => (
            <button 
              key={p} 
              onClick={() => setCurrentPage(p)}
              className={"w-full p-2 rounded-lg border text-left text-[12px] transition-colors " + (p === currentPage ? "border-primary-500 bg-primary-50" : "border-border-subtle hover:border-border-default")}
            >
              <div className="w-full h-32 bg-bg-surface-tint rounded mb-1 flex items-center justify-center overflow-hidden">
                {pageImageUrls[p] ? (
                  <img src={pageImageUrls[p]} alt={`Page ${p} thumbnail`} className="object-contain h-full w-full" />
                ) : (
                  <span className="text-[10px] text-text-subtle">Page {p}</span>
                )}
              </div>
            </button>
          ))}
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="bg-bg-surface-tint rounded-xl border border-border-subtle h-[600px] flex items-center justify-center overflow-hidden">
              {pageImageUrls[currentPage] ? (
                <img src={pageImageUrls[currentPage]} alt={`Page ${currentPage}`} className="object-contain h-full w-full" />
              ) : (
                <div className="text-center">
                  <FileText className="w-20 h-20 text-text-subtle mx-auto mb-3" />
                  <p className="text-[14px] text-text-muted">Loading Preview...</p>
                  <p className="text-[12px] text-text-subtle">Page {currentPage} of {totalPages}</p>
                </div>
              )}
            </div>
            <div className="flex items-center justify-between mt-4">
              <Button variant="outline" size="icon" className="h-8 w-8" disabled={currentPage <= 1} onClick={() => setCurrentPage(c => c - 1)}>
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-[12px] text-text-muted">Page {currentPage} / {totalPages}</span>
              <Button variant="outline" size="icon" className="h-8 w-8" disabled={currentPage >= totalPages} onClick={() => setCurrentPage(c => c + 1)}>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
