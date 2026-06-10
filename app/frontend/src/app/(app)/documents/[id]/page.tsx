"use client";

import { use } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";

export default function DocumentPreviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/documents"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div>
          <h1 className="text-h1 text-text-strong">Admission Note - May 2025</h1>
          <p className="text-caption text-text-muted">Document ID: {id} · 3 pages · Indexed</p>
        </div>
        <Badge variant="outline" className="bg-success-50 text-success-600 ml-2">OCR: 94%</Badge>
      </div>

      <div className="grid grid-cols-[176px_1fr] gap-4">
        <div className="space-y-2">
          {[1, 2, 3].map((p) => (
            <button key={p} className={"w-full p-2 rounded-lg border text-left text-[12px] transition-colors " + (p === 1 ? "border-primary-500 bg-primary-50" : "border-border-subtle hover:border-border-default")}>
              <div className="w-full h-24 bg-bg-surface-tint rounded mb-1 flex items-center justify-center text-[10px] text-text-subtle">Page {p}</div>
            </button>
          ))}
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="bg-bg-surface-tint rounded-xl border border-border-subtle h-[600px] flex items-center justify-center">
              <div className="text-center"><FileText className="w-20 h-20 text-text-subtle mx-auto mb-3" /><p className="text-[14px] text-text-muted">Document Preview</p><p className="text-[12px] text-text-subtle">Page 1 of 3</p></div>
            </div>
            <div className="flex items-center justify-between mt-4">
              <Button variant="outline" size="icon" className="h-8 w-8" disabled><ChevronLeft className="w-4 h-4" /></Button>
              <span className="text-[12px] text-text-muted">Page 1 / 3</span>
              <Button variant="outline" size="icon" className="h-8 w-8"><ChevronRight className="w-4 h-4" /></Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
