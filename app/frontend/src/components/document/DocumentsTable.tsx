import { Badge } from "@/components/ui/badge";
import { FileText, MoreHorizontal } from "lucide-react";
import Link from "next/link";

interface DocumentRow {
  id: string;
  title: string;
  patientName?: string;
  documentType: string;
  status: string;
  ocrConfidence?: number;
  pageCount?: number;
  createdAt: string;
}

interface DocumentsTableProps {
  documents: DocumentRow[];
}

const STATUS_COLORS: Record<string, string> = {
  indexed: "bg-success-50 text-success-600",
  processing: "bg-warning-50 text-warning-500",
  failed: "bg-danger-50 text-danger-600",
  uploaded: "bg-primary-50 text-primary-600",
  ready: "bg-success-50 text-success-600",
};

export function DocumentsTable({ documents }: DocumentsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead><tr className="border-b border-border-subtle">
          <th className="text-left py-3 px-3 text-[12px] font-semibold text-text-muted">Name</th>
          <th className="text-left py-3 px-3 text-[12px] font-semibold text-text-muted">Patient</th>
          <th className="text-left py-3 px-3 text-[12px] font-semibold text-text-muted">Type</th>
          <th className="text-left py-3 px-3 text-[12px] font-semibold text-text-muted">Status</th>
          <th className="text-left py-3 px-3 text-[12px] font-semibold text-text-muted">OCR Conf.</th>
          <th className="text-left py-3 px-3 text-[12px] font-semibold text-text-muted">Date</th>
          <th className="w-10"></th>
        </tr></thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id} className="border-b border-border-subtle hover:bg-bg-surface-tint transition-colors">
              <td className="py-3 px-3"><Link href={"/documents/" + doc.id} className="flex items-center gap-2 text-[13px] font-medium text-text-default hover:text-primary-600"><FileText className="w-3.5 h-3.5 text-text-subtle" />{doc.title}</Link></td>
              <td className="py-3 px-3 text-[13px] text-text-muted">{doc.patientName || "—"}</td>
              <td className="py-3 px-3 text-[13px] text-text-muted">{doc.documentType}</td>
              <td className="py-3 px-3"><Badge variant="outline" className={STATUS_COLORS[doc.status] || "bg-bg-surface-tint text-text-muted"}>{doc.status}</Badge></td>
              <td className="py-3 px-3 text-[13px] text-text-muted">{doc.ocrConfidence ? Math.round(doc.ocrConfidence * 100) + "%" : "—"}</td>
              <td className="py-3 px-3 text-[13px] text-text-muted">{doc.createdAt}</td>
              <td className="py-3 px-3"><button className="p-1 rounded hover:bg-bg-surface-tint"><MoreHorizontal className="w-3.5 h-3.5 text-text-subtle" /></button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
