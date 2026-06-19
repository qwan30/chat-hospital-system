export interface AccessRequest {
  id: string;
  patient: string;
  mrn: string;
  requester: string;
  role: string;
  unit: string;
  justification: string;
  status: "pending" | "approved" | "denied";
  ts: string;
  reviewer?: string;
  decisionTs?: string;
}

export const accessRequests: AccessRequest[] = [
  {
    id: "ar-001",
    patient: "Yuki Tanaka",
    mrn: "MRN-48577",
    requester: "Dr. Sarah Chen",
    role: "Cardiologist",
    unit: "Cardiology · 4N",
    justification: "Cross-consult requested by primary team for HTN co-management.",
    status: "pending",
    ts: "2026-06-12T15:42:00Z",
  },
  {
    id: "ar-002",
    patient: "Amelia Brooks",
    mrn: "MRN-48994",
    requester: "Dr. Sarah Chen",
    role: "Cardiologist",
    unit: "OB-GYN · 5E",
    justification: "Hypertensive emergency in pregnancy. Cardiology consult requested.",
    status: "approved",
    ts: "2026-06-12T13:10:00Z",
    reviewer: "Admin J. Kim",
    decisionTs: "2026-06-12T13:24:00Z",
  },
  {
    id: "ar-003",
    patient: "Aisha Mahmoud",
    mrn: "MRN-49340",
    requester: "Dr. L. Garcia",
    role: "Hospitalist",
    unit: "Oncology · 7N",
    justification: "Patient transferred to internal medicine for symptom management.",
    status: "denied",
    ts: "2026-06-12T11:02:00Z",
    reviewer: "Admin J. Kim",
    decisionTs: "2026-06-12T11:30:00Z",
  },
  {
    id: "ar-004",
    patient: "David Müller",
    mrn: "MRN-48201",
    requester: "Nurse R. Owens",
    role: "RN",
    unit: "ICU · 2W",
    justification: "Bedside RN access for ongoing post-op monitoring overnight.",
    status: "pending",
    ts: "2026-06-12T16:01:00Z",
  },
  {
    id: "ar-005",
    patient: "Hassan Karimi",
    mrn: "MRN-49011",
    requester: "Dr. M. Patel",
    role: "Cardiologist",
    unit: "Endo · 3N",
    justification: "Diabetic cardiomyopathy workup; reviewing recent echos.",
    status: "approved",
    ts: "2026-06-11T22:14:00Z",
    reviewer: "Admin J. Kim",
    decisionTs: "2026-06-11T22:40:00Z",
  },
];

export function getAccessRequest(id: string) {
  return accessRequests.find((r) => r.id === id);
}
