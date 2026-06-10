import { Upload } from "lucide-react";

export function UploadDropzoneCompact({ onFilesSelected }: { onFilesSelected: (files: FileList) => void }) {
  return (
    <div className="relative">
      <input type="file" multiple accept=".pdf,.jpg,.png" onChange={(e) => e.target.files && onFilesSelected(e.target.files)} className="absolute inset-0 opacity-0 cursor-pointer" />
      <div className="flex flex-col items-center py-6 px-4 border-2 border-dashed border-border-default rounded-lg bg-bg-surface-tint hover:border-primary-300 transition-colors">
        <Upload className="w-6 h-6 text-primary-400 mb-2" />
        <p className="text-[13px] font-medium text-text-default">Drop files or click</p>
        <p className="text-[11px] text-text-subtle">PDF, JPG, PNG</p>
      </div>
    </div>
  );
}
