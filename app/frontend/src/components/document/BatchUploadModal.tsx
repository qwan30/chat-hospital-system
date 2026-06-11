import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { UploadDropzoneCompact } from "./UploadDropzoneCompact";
import { OCRPipelineStepper } from "./OCRPipelineStepper";
import { FileText, CheckCircle, Upload } from "lucide-react";
import { toast } from "sonner";
import { useState, useRef } from "react";

interface FileItem { name: string; progress: number; status: "waiting" | "uploading" | "done" | "error"; }

interface BatchUploadModalProps { open: boolean; onClose: () => void; }

export function BatchUploadModal({ open, onClose }: BatchUploadModalProps) {
  const [step, setStep] = useState(0);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const intervalsRef = useRef<NodeJS.Timeout[]>([]);

  const handleFiles = (fl: FileList) => {
    setFiles(Array.from(fl).map((f) => ({ name: f.name, progress: 0, status: "waiting" as const })));
    setStep(1);
  };

  function startUpload() {
    setUploading(true);
    setFiles(prev => prev.map(f => ({ ...f, status: "uploading" as const })));

    files.forEach((_, i) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15 + 5;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          setFiles(prev => prev.map((f, j) => j === i ? { ...f, progress: 100, status: "done" as const } : f));
          setFiles(prev => {
            if (prev.every(f => f.status === "done")) {
              setUploading(false);
              toast.success("All files uploaded successfully.");
            }
            return prev;
          });
        } else {
          setFiles(prev => prev.map((f, j) => j === i ? { ...f, progress } : f));
        }
        intervalsRef.current = intervalsRef.current.filter(iv => iv !== interval);
      }, 200);
      intervalsRef.current.push(interval);
    });
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader><DialogTitle>Upload Documents</DialogTitle></DialogHeader>
        <div className="space-y-4 mt-4">
          <OCRPipelineStepper currentStep={step} />
          {step === 0 && <UploadDropzoneCompact onFilesSelected={handleFiles} />}
          {step >= 1 && <div className="space-y-2">{files.map((f, i) => <div key={i} className="flex items-center gap-3 p-2 bg-bg-surface-tint rounded-lg"><FileText className="w-4 h-4 text-text-subtle" /><span className="text-[13px] flex-1 truncate">{f.name}</span>{f.status === "done" ? <CheckCircle className="w-4 h-4 text-success-500" /> : <Progress value={f.progress} className="w-20 h-1.5" />}</div>)}</div>}
          <div className="flex justify-end gap-3">
            {files.every(f => f.status === "done") && files.length > 0 ? (
              <>
                <span className="text-[13px] text-success-600 self-center flex items-center gap-1"><CheckCircle className="w-4 h-4" />Upload Complete</span>
                <Button onClick={onClose}>Done</Button>
              </>
            ) : (
              <>
                <Button variant="outline" onClick={onClose} disabled={uploading}>Cancel</Button>
                <Button disabled={files.length === 0 || uploading} onClick={startUpload}>
                  <Upload className="w-4 h-4 mr-2" />{uploading ? "Uploading..." : `Upload ${files.length} files`}
                </Button>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
