import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { UploadDropzoneCompact } from "./UploadDropzoneCompact";
import { OCRPipelineStepper } from "./OCRPipelineStepper";
import { FileText, CheckCircle, Upload } from "lucide-react";
import { useState } from "react";

interface BatchUploadModalProps { open: boolean; onClose: () => void; }

export function BatchUploadModal({ open, onClose }: BatchUploadModalProps) {
  const [step, setStep] = useState(0);
  const [files, setFiles] = useState<{ name: string; progress: number }[]>([]);

  const handleFiles = (fl: FileList) => {
    setFiles(Array.from(fl).map((f) => ({ name: f.name, progress: 0 })));
    setStep(1);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader><DialogTitle>Upload Documents</DialogTitle></DialogHeader>
        <div className="space-y-4 mt-4">
          <OCRPipelineStepper currentStep={step} />
          {step === 0 && <UploadDropzoneCompact onFilesSelected={handleFiles} />}
          {step >= 1 && <div className="space-y-2">{files.map((f, i) => <div key={i} className="flex items-center gap-3 p-2 bg-bg-surface-tint rounded-lg"><FileText className="w-4 h-4 text-text-subtle" /><span className="text-[13px] flex-1 truncate">{f.name}</span><Progress value={f.progress} className="w-20 h-1.5" /></div>)}</div>}
          <div className="flex justify-end gap-3"><Button variant="outline" onClick={onClose}>Cancel</Button><Button disabled={files.length === 0}><Upload className="w-4 h-4 mr-2" />Upload {files.length} files</Button></div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
