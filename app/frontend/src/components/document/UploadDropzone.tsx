import { Upload, FileText } from "lucide-react";

interface UploadDropzoneProps {
  onFilesSelected: (files: FileList) => void;
}

export function UploadDropzone({ onFilesSelected }: UploadDropzoneProps) {
  return (
    <div className="relative">
      <input type="file" multiple accept=".pdf,.jpg,.png,.tiff,.dcm" onChange={(e) => e.target.files && onFilesSelected(e.target.files)} className="absolute inset-0 opacity-0 cursor-pointer" />
      <div className="flex flex-col items-center py-10 px-6 border-2 border-dashed border-default rounded-xl bg-bg-surface-tint hover:border-primary-300 hover:bg-primary-50/50 transition-colors">
        <Upload className="w-10 h-10 text-primary-400 mb-3" />
        <p className="text-[14px] font-semibold text-text-default mb-1">Drop files here or click to browse</p>
        <p className="text-[12px] text-text-muted">Supports PDF, JPG, PNG, TIFF, DICOM</p>
      </div>
    </div>
  );
}
