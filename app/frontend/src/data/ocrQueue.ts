export interface OcrJob {
  id: string;
  file: string;
  size: string;
  pages: number;
  status: "queued" | "processing" | "review" | "indexed" | "failed";
  confidence: number;
  ts: string;
  documentId?: string;
  error?: string;
}

export const ocrQueue: OcrJob[] = [
  { id: "o-001", file: "Echo-Report-2026-06-11.pdf", size: "1.4 MB", pages: 4, status: "indexed", confidence: 0.97, ts: "2026-06-12T13:02:00Z", documentId: "d-04" },
  { id: "o-002", file: "Discharge-Summary-Vance.pdf", size: "820 KB", pages: 2, status: "processing", confidence: 0.0, ts: "2026-06-12T16:08:00Z" },
  { id: "o-003", file: "Lab-Panel-CBC-CMP.pdf", size: "210 KB", pages: 1, status: "review", confidence: 0.62, ts: "2026-06-12T15:50:00Z", documentId: "d-09" },
  { id: "o-004", file: "Cath-Report-Okafor.pdf", size: "2.1 MB", pages: 6, status: "queued", confidence: 0, ts: "2026-06-12T16:10:00Z" },
  { id: "o-005", file: "OR-Note-Müller.tiff", size: "5.6 MB", pages: 8, status: "failed", confidence: 0.18, ts: "2026-06-12T15:20:00Z", error: "Low contrast scan; cannot extract structured fields." },
  { id: "o-006", file: "Pharmacy-Formulary-2026.pdf", size: "3.8 MB", pages: 142, status: "indexed", confidence: 0.99, ts: "2026-06-11T22:14:00Z", documentId: "d-12" },
  { id: "o-007", file: "Sepsis-Bundle-Protocol.docx", size: "78 KB", pages: 3, status: "indexed", confidence: 0.99, ts: "2026-06-11T18:00:00Z", documentId: "d-02" },
  { id: "o-008", file: "CXR-Petersen-2026-06-12.jpg", size: "4.2 MB", pages: 1, status: "review", confidence: 0.71, ts: "2026-06-12T05:02:00Z" },
];

export function getOcrJob(id: string) {
  return ocrQueue.find((j) => j.id === id);
}