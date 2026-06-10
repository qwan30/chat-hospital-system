"use client";

import { use } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { OCRPipelineStepper } from "@/components/document/OCRPipelineStepper";
import { FileText, AlertTriangle, CheckCircle, ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";

export default function OCRReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/documents"><Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button></Link>
        <div><h1 className="text-h1 text-text-strong">OCR Review</h1><p className="text-caption text-text-muted">Document {id}</p></div>
      </div>

      <OCRPipelineStepper currentStep={2} />

      <div className="flex items-center gap-2 p-3 rounded-lg bg-warning-50 border border-warning-100">
        <AlertTriangle className="w-4 h-4 text-warning-500 flex-shrink-0" />
        <p className="text-[13px] text-warning-700">Low OCR confidence detected on 3 sections. Please review highlighted areas.</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-h4">Scanned Page</CardTitle></CardHeader>
          <CardContent>
            <div className="bg-bg-surface-tint rounded-xl border border-border-subtle h-[500px] flex items-center justify-center">
              <div className="text-center"><FileText className="w-16 h-16 text-text-subtle mx-auto mb-3" /><p className="text-[14px] text-text-muted">Scanned document preview</p><p className="text-[12px] text-text-subtle">Page 1 of 3</p></div>
            </div>
            <div className="flex items-center justify-between mt-3">
              <Button variant="outline" size="icon" className="h-8 w-8"><ChevronLeft className="w-4 h-4" /></Button>
              <span className="text-[12px] text-text-muted">Page 1 / 3</span>
              <Button variant="outline" size="icon" className="h-8 w-8"><ChevronRight className="w-4 h-4" /></Button>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-h4">Extracted Text</CardTitle></CardHeader>
          <CardContent>
            <div className="bg-bg-surface-tint rounded-xl border border-border-subtle p-4 h-[500px] overflow-y-auto">
              <div className="space-y-3 text-[13px] leading-relaxed">
                <p className="text-text-default"><span className="bg-warning-100 text-warning-700 px-0.5 rounded">PATIENT NAME: JONATHAN BLAKE</span></p>
                <p className="text-text-default">MRN: MR-2025-0847</p>
                <p className="text-text-default">DOB: 03/15/1962</p>
                <p className="text-text-default">Date of Admission: <span className="bg-warning-100 text-warning-700 px-0.5 rounded">05/12/2025</span></p>
                <p className="text-text-default mt-3">CHIEF COMPLAINT:</p>
                <p className="text-text-default">Patient presents with acute chest pain radiating to the left arm, onset approximately 2 hours prior to admission. Pain described as pressure-like, <span className="bg-warning-100 text-warning-700 px-0.5 rounded">8/10</span> severity.</p>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <Button className="gap-2"><CheckCircle className="w-4 h-4" />Confirm & Index</Button>
              <Button variant="outline">Edit Corrections</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
