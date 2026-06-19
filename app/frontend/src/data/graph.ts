export interface GraphNode {
  id: string;
  type: "patient" | "encounter" | "diagnosis" | "medication" | "allergy" | "lab";
  label: string;
  sublabel?: string;
  x: number;
  y: number;
}
export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  label: string;
}
export interface GraphData {
  patientId: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const patientGraph: GraphData = {
  patientId: "p-001",
  nodes: [
    {
      id: "pt",
      type: "patient",
      label: "Eleanor Vance",
      sublabel: "MRN-48201 · 72F",
      x: 400,
      y: 240,
    },
    { id: "e1", type: "encounter", label: "Admission", sublabel: "Jun 8, 2026", x: 180, y: 120 },
    {
      id: "e2",
      type: "encounter",
      label: "Cardio consult",
      sublabel: "Jun 10, 2026",
      x: 180,
      y: 360,
    },
    {
      id: "d1",
      type: "diagnosis",
      label: "Atrial fibrillation",
      sublabel: "I48.0",
      x: 620,
      y: 100,
    },
    { id: "d2", type: "diagnosis", label: "CHF, preserved EF", sublabel: "I50.32", x: 620, y: 240 },
    { id: "d3", type: "diagnosis", label: "CKD stage 3", sublabel: "N18.3", x: 620, y: 380 },
    { id: "m1", type: "medication", label: "Apixaban", sublabel: "5mg BID", x: 820, y: 100 },
    { id: "m2", type: "medication", label: "Metoprolol", sublabel: "50mg BID", x: 820, y: 220 },
    { id: "m3", type: "medication", label: "Furosemide", sublabel: "40mg daily", x: 820, y: 340 },
    { id: "a1", type: "allergy", label: "Sulfa drugs", sublabel: "rash, 2014", x: 60, y: 240 },
    { id: "l1", type: "lab", label: "BNP 612", sublabel: "Jun 11", x: 400, y: 60 },
    { id: "l2", type: "lab", label: "Creatinine 1.6", sublabel: "Jun 11", x: 400, y: 420 },
  ],
  edges: [
    { id: "e-pt-e1", from: "pt", to: "e1", label: "had" },
    { id: "e-pt-e2", from: "pt", to: "e2", label: "had" },
    { id: "e-e1-d1", from: "e1", to: "d1", label: "diagnosed" },
    { id: "e-e1-d2", from: "e1", to: "d2", label: "diagnosed" },
    { id: "e-e2-d3", from: "e2", to: "d3", label: "noted" },
    { id: "e-d1-m1", from: "d1", to: "m1", label: "treats" },
    { id: "e-d2-m2", from: "d2", to: "m2", label: "treats" },
    { id: "e-d2-m3", from: "d2", to: "m3", label: "treats" },
    { id: "e-pt-a1", from: "pt", to: "a1", label: "allergic to" },
    { id: "e-pt-l1", from: "pt", to: "l1", label: "result" },
    { id: "e-pt-l2", from: "pt", to: "l2", label: "result" },
  ],
};

export interface GraphPath {
  id: string;
  rationale: string;
  steps: { from: string; to: string; relation: string; evidence: string }[];
}
export const graphPaths: GraphPath[] = [
  {
    id: "path-001",
    rationale:
      "Selected because the query asked 'why apixaban for this patient' — traversal: Patient → Diagnosis (AFib) → Medication (Apixaban). CKD considered as cofactor.",
    steps: [
      {
        from: "Eleanor Vance",
        to: "Atrial fibrillation (I48.0)",
        relation: "diagnosed at admission Jun 8",
        evidence: "Admit note, Dr. M. Patel",
      },
      {
        from: "Atrial fibrillation",
        to: "Apixaban 5mg BID",
        relation: "guideline-directed anticoagulation",
        evidence: "ACC/AHA AFib 2023, CHA2DS2-VASc=4",
      },
      {
        from: "Apixaban",
        to: "CKD stage 3",
        relation: "renal dose adjustment evaluated",
        evidence: "Cr 1.6, eGFR 42 — standard 5mg BID retained",
      },
    ],
  },
];

export function getGraphPath(id: string) {
  return graphPaths.find((p) => p.id === id);
}
