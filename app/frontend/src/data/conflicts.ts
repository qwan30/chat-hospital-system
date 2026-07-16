export interface DrugConflict {
  id: string;
  patient: string;
  patientId: string;
  drug: string;
  conflictsWith: string;
  type: "allergy" | "interaction" | "renal" | "duplicate";
  severity: "low" | "moderate" | "high" | "critical";
  rule: string;
  source: string;
  recommendation: string;
  status: "open" | "ack" | "overridden";
  ts: string;
}

export const drugConflicts: DrugConflict[] = [
  {
    id: "c-001",
    patient: "Eleanor Vance",
    patientId: "11111111-1111-1111-1111-111111111111",
    drug: "Amiodarone 200mg PO daily",
    conflictsWith: "Warfarin 5mg PO daily",
    type: "interaction",
    severity: "high",
    rule: "Amiodarone potentiates warfarin → ↑INR",
    source: "Lexicomp Drug Interactions 2026.4",
    recommendation: "Reduce warfarin dose 30-50% and recheck INR in 3-5 days.",
    status: "open",
    ts: "2026-06-12T16:00:00Z",
  },
  {
    id: "c-002",
    patient: "Priya Raman",
    patientId: "p-004",
    drug: "Ibuprofen 600mg PRN",
    conflictsWith: "CKD stage 3 (eGFR 42)",
    type: "renal",
    severity: "high",
    rule: "NSAIDs contraindicated when eGFR < 60 in CHF",
    source: "KDIGO 2024 Guidelines",
    recommendation: "Use acetaminophen instead. Avoid NSAIDs.",
    status: "open",
    ts: "2026-06-12T14:32:00Z",
  },
  {
    id: "c-003",
    patient: "Marcus Okafor",
    patientId: "22222222-2222-2222-2222-222222222222",
    drug: "Penicillin G 5 MU IV q6h",
    conflictsWith: "Documented penicillin allergy (hives, 2018)",
    type: "allergy",
    severity: "critical",
    rule: "Beta-lactam allergy match",
    source: "Patient allergy chart",
    recommendation: "Switch to vancomycin or clindamycin. Confirm allergy severity.",
    status: "ack",
    ts: "2026-06-12T11:20:00Z",
  },
  {
    id: "c-004",
    patient: "Hassan Karimi",
    patientId: "p-007",
    drug: "Metformin 1g BID",
    conflictsWith: "Contrast study scheduled tomorrow",
    type: "interaction",
    severity: "moderate",
    rule: "Hold metformin 48h pre/post IV contrast (eGFR < 60)",
    source: "ACR Manual on Contrast Media v2024",
    recommendation: "Hold metformin starting today. Resume 48h post-contrast.",
    status: "open",
    ts: "2026-06-12T10:00:00Z",
  },
  {
    id: "c-005",
    patient: "Noah Petersen",
    patientId: "p-011",
    drug: "Heparin gtt",
    conflictsWith: "Apixaban 5mg BID (home med)",
    type: "duplicate",
    severity: "moderate",
    rule: "Overlapping anticoagulation increases bleeding risk",
    source: "Internal pharmacy protocol HP-127",
    recommendation: "Hold apixaban while on heparin gtt. Document plan.",
    status: "overridden",
    ts: "2026-06-11T22:00:00Z",
  },
];

export function getConflict(id: string) {
  return drugConflicts.find((c) => c.id === id);
}
