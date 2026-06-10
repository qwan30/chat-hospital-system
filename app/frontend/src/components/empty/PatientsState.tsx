import { Users, Search, Upload } from "lucide-react";
import Link from "next/link";

export function PatientsState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6">
      <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mb-5">
        <Users className="w-8 h-8 text-primary-400" />
      </div>
      <h2 className="text-h2 text-text-strong mb-2">No patients found</h2>
      <p className="text-body text-text-muted max-w-md text-center mb-6">
        No patient records match your current search. Try adjusting your filters or upload new patient documents to get started.
      </p>
      <div className="flex items-center gap-3">
        <Link
          href="/documents/upload"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-[14px] font-semibold rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Upload className="w-4 h-4" />
          Upload Documents
        </Link>
        <button
          onClick={() => window.history.back()}
          className="inline-flex items-center gap-2 px-4 py-2 border border-border-default text-text-default text-[14px] font-medium rounded-lg hover:bg-bg-surface-tint transition-colors"
        >
          <Search className="w-4 h-4" />
          Adjust Search
        </button>
      </div>
    </div>
  );
}
