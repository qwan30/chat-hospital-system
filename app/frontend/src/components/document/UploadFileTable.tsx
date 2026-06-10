import { FileText, X, CheckCircle, Loader2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface UploadFile { name: string; size: string; progress: number; status: "uploading" | "done" | "error"; }

export function UploadFileTable({ files, onRemove }: { files: UploadFile[]; onRemove?: (i: number) => void }) {
  return (
    <div className="space-y-2">
      {files.map((f, i) => (
        <div key={i} className="flex items-center gap-3 p-3 bg-bg-surface-tint rounded-lg border border-border-subtle">
          <FileText className="w-4 h-4 text-text-subtle flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1"><span className="text-[13px] font-medium truncate">{f.name}</span><span className="text-[11px] text-text-subtle ml-2">{f.size}</span></div>
            {f.status === "uploading" && <Progress value={f.progress} className="h-1.5" />}
          </div>
          {f.status === "uploading" && <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />}
          {f.status === "done" && <CheckCircle className="w-4 h-4 text-success-500" />}
          {f.status === "error" && <X className="w-4 h-4 text-danger-500" />}
          {onRemove && <button onClick={() => onRemove(i)} className="text-text-subtle hover:text-text-muted"><X className="w-3.5 h-3.5" /></button>}
        </div>
      ))}
    </div>
  );
}
