import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { FileText, ChevronLeft, ChevronRight, X } from "lucide-react";
import { useState } from "react";

interface DocumentViewerModalProps {
  open: boolean;
  onClose: () => void;
  documentTitle: string;
  pageCount?: number;
}

export function DocumentViewerModal({ open, onClose, documentTitle, pageCount = 3 }: DocumentViewerModalProps) {
  const [currentPage, setCurrentPage] = useState(1);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[900px] h-[80vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-h2 flex items-center gap-2"><FileText className="w-5 h-5" />{documentTitle}</DialogTitle>
        </DialogHeader>
        <div className="flex-1 grid grid-cols-[176px_1fr_220px] gap-4 min-h-0">
          <div className="space-y-2 overflow-y-auto pr-1">
            {Array.from({ length: pageCount }, (_, i) => (
              <button key={i} onClick={() => setCurrentPage(i + 1)} className={"w-full p-2 rounded-lg border text-left text-[12px] transition-colors " + (currentPage === i + 1 ? "border-primary-500 bg-primary-50" : "border-border-subtle hover:border-border-default")}>
                <div className="w-full h-20 bg-bg-surface-tint rounded mb-1 flex items-center justify-center text-[10px] text-text-subtle">Page {i + 1}</div>
              </button>
            ))}
          </div>
          <div className="bg-bg-surface-tint rounded-xl border border-border-subtle flex items-center justify-center">
            <div className="text-center"><FileText className="w-12 h-12 text-text-subtle mx-auto mb-2" /><p className="text-[14px] text-text-muted">Document Preview</p><p className="text-[12px] text-text-subtle">Page {currentPage} of {pageCount}</p></div>
          </div>
          <div className="space-y-3 overflow-y-auto">
            <h4 className="text-h4 text-text-strong">Citation Details</h4>
            <div className="space-y-2">
              <div><span className="text-[11px] text-text-subtle">Source</span><p className="text-[13px] text-text-default">{documentTitle}</p></div>
              <div><span className="text-[11px] text-text-subtle">Page</span><p className="text-[13px] text-text-default">{currentPage}</p></div>
              <div><span className="text-[11px] text-text-subtle">Confidence</span><Badge variant="outline" className="bg-success-50 text-success-600 text-[10px]">High</Badge></div>
            </div>
            <div className="p-3 bg-bg-surface-tint rounded-lg border border-border-subtle">
              <p className="text-[12px] text-text-muted leading-relaxed italic">...patient presented with acute chest pain radiating to the left arm. EKG showed ST elevation in leads II, III, and aVF...</p>
            </div>
            <div className="flex items-center justify-between pt-2">
              <button onClick={() => setCurrentPage(Math.max(1, currentPage - 1))} disabled={currentPage === 1} className="p-1.5 rounded hover:bg-bg-surface-tint disabled:opacity-30"><ChevronLeft className="w-4 h-4" /></button>
              <span className="text-[12px] text-text-muted">{currentPage}/{pageCount}</span>
              <button onClick={() => setCurrentPage(Math.min(pageCount, currentPage + 1))} disabled={currentPage === pageCount} className="p-1.5 rounded hover:bg-bg-surface-tint disabled:opacity-30"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
