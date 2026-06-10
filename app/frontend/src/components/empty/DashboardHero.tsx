import { LayoutDashboard, Upload, Search } from "lucide-react";
import Link from "next/link";

export function DashboardHero() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6">
      <div className="w-20 h-20 rounded-2xl bg-primary-50 flex items-center justify-center mb-6">
        <LayoutDashboard className="w-10 h-10 text-primary-400" />
      </div>
      <h2 className="text-h2 text-text-strong mb-3">Welcome to Your Dashboard</h2>
      <p className="text-body text-text-muted max-w-lg text-center mb-8">Get started by uploading patient documents or searching for existing records. Your AI-powered clinical assistant is ready to help.</p>
      <div className="flex items-center gap-3">
        <Link href="/documents/upload" className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white text-[14px] font-semibold rounded-lg hover:bg-primary-700 transition-colors"><Upload className="w-4 h-4" />Upload Documents</Link>
        <Link href="/patients" className="inline-flex items-center gap-2 px-5 py-2.5 border border-border-default text-text-default text-[14px] font-medium rounded-lg hover:bg-bg-surface-tint transition-colors"><Search className="w-4 h-4" />Search Patients</Link>
      </div>
    </div>
  );
}
