export interface DocItem {
  id: string;
  name: string;
  type: "PDF" | "DOCX" | "Scan" | "Image" | "HL7";
  category: "Guideline" | "Protocol" | "Discharge" | "Lab" | "Imaging" | "Note";
  size: string;
  uploadedBy: string;
  uploaded: string;
  status: "indexed" | "processing" | "queued" | "ocr" | "error";
  pages: number;
}

export const documents: DocItem[] = [
  { id: "d-01", name: "ACC-AHA-AF-Guideline-2024.pdf", type: "PDF", category: "Guideline", size: "4.2 MB", uploadedBy: "Records Bot", uploaded: "Today, 09:01", status: "indexed", pages: 218 },
  { id: "d-02", name: "HFrEF-GDMT-Protocol-v3.2.pdf", type: "PDF", category: "Protocol", size: "1.1 MB", uploadedBy: "Dr. Patel", uploaded: "Today, 08:32", status: "indexed", pages: 24 },
  { id: "d-03", name: "ECHO-48201-Vance.dcm.pdf", type: "PDF", category: "Imaging", size: "812 KB", uploadedBy: "Imaging Auto-Sync", uploaded: "Today, 07:14", status: "indexed", pages: 6 },
  { id: "d-04", name: "Sepsis-Bundle-2026.docx", type: "DOCX", category: "Protocol", size: "246 KB", uploadedBy: "Dr. Liu", uploaded: "Today, 06:48", status: "processing", pages: 18 },
  { id: "d-05", name: "Discharge-Summary-Okafor.pdf", type: "PDF", category: "Discharge", size: "522 KB", uploadedBy: "Records Bot", uploaded: "Today, 06:12", status: "indexed", pages: 4 },
  { id: "d-06", name: "Scanned-Consult-Müller.jpg", type: "Scan", category: "Note", size: "3.4 MB", uploadedBy: "Front Desk", uploaded: "Today, 05:55", status: "ocr", pages: 2 },
  { id: "d-07", name: "Lab-Panel-19022.hl7", type: "HL7", category: "Lab", size: "12 KB", uploadedBy: "Core Lab", uploaded: "Yesterday", status: "indexed", pages: 1 },
  { id: "d-08", name: "DOAC-Renal-Dosing.pdf", type: "PDF", category: "Protocol", size: "188 KB", uploadedBy: "Pharmacy", uploaded: "Yesterday", status: "indexed", pages: 8 },
  { id: "d-09", name: "Old-Faxed-Referral.pdf", type: "PDF", category: "Note", size: "1.8 MB", uploadedBy: "Front Desk", uploaded: "Yesterday", status: "error", pages: 0 },
  { id: "d-10", name: "Breast-CA-Pathway.docx", type: "DOCX", category: "Protocol", size: "412 KB", uploadedBy: "Oncology", uploaded: "2d ago", status: "indexed", pages: 32 },
  { id: "d-11", name: "Imaging-MRI-Lin.pdf", type: "PDF", category: "Imaging", size: "2.6 MB", uploadedBy: "Imaging Auto-Sync", uploaded: "2d ago", status: "indexed", pages: 5 },
  { id: "d-12", name: "Hospital-Formulary-2026.pdf", type: "PDF", category: "Guideline", size: "11.4 MB", uploadedBy: "Pharmacy", uploaded: "3d ago", status: "indexed", pages: 482 },
  { id: "d-13", name: "Stroke-Workflow.docx", type: "DOCX", category: "Protocol", size: "98 KB", uploadedBy: "Dr. Chen", uploaded: "3d ago", status: "queued", pages: 6 },
  { id: "d-14", name: "Progress-Note-Raman.pdf", type: "PDF", category: "Note", size: "320 KB", uploadedBy: "Dr. Chen", uploaded: "4d ago", status: "indexed", pages: 2 },
  { id: "d-15", name: "ICU-Vasopressor-Protocol.pdf", type: "PDF", category: "Protocol", size: "740 KB", uploadedBy: "ICU", uploaded: "5d ago", status: "indexed", pages: 14 },
];