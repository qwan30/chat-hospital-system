export interface CitationSource {
  id: string;
  title: string;
  type: "Guideline" | "Lab Result" | "Imaging Report" | "Progress Note" | "Discharge Summary" | "Protocol";
  source: string;
  date: string;
  page?: number;
  snippet: string;
  body: string;
  relevance: number;
}

export const citations: Record<string, CitationSource> = {
  "c-001": {
    id: "c-001",
    title: "ACC/AHA Guideline for Management of Atrial Fibrillation",
    type: "Guideline",
    source: "ACC/AHA 2023 · Section 7.2",
    date: "Jan 2024",
    page: 142,
    snippet:
      "In patients with AF and a CHA2DS2-VASc score ≥2 in men or ≥3 in women, oral anticoagulation is recommended (Class 1, LOE A).",
    body:
      "7.2 Stroke prevention. In patients with nonvalvular atrial fibrillation and a CHA2DS2-VASc score ≥2 in men or ≥3 in women, oral anticoagulation is recommended to reduce the risk of stroke and systemic thromboembolism (Class 1, Level of Evidence: A). Direct oral anticoagulants (DOACs) are preferred over warfarin in DOAC-eligible patients (Class 1, LOE A). For patients with mechanical heart valves or moderate-to-severe mitral stenosis, warfarin remains the standard of care.",
    relevance: 0.96,
  },
  "c-002": {
    id: "c-002",
    title: "Echocardiogram — Vance, E. 2026-06-08",
    type: "Imaging Report",
    source: "Cardiology Imaging · Study #ECHO-48201",
    date: "Jun 8, 2026",
    snippet:
      "Left atrial volume index 38 mL/m². Mild mitral regurgitation. LVEF 52%. No intracardiac thrombus visualized.",
    body:
      "Transthoracic echocardiogram. LVEF estimated at 52% by biplane Simpson method. Left atrium moderately dilated (LAVI 38 mL/m²). Mild mitral regurgitation. Trace tricuspid regurgitation. No pericardial effusion. No intracardiac thrombus visualized. RVSP estimated 28 mmHg. Interpretation: preserved LV systolic function with LA enlargement consistent with chronic AF.",
    relevance: 0.88,
  },
  "c-003": {
    id: "c-003",
    title: "Progress Note — Vance, E. 2026-06-10",
    type: "Progress Note",
    source: "Dr. M. Patel · Cardiology",
    date: "Jun 10, 2026",
    snippet:
      "Patient reports palpitations 2x/week. HR 78, rhythm irregular. Continue apixaban 5mg BID. CHA2DS2-VASc = 4.",
    body:
      "S: Patient reports intermittent palpitations approximately twice weekly, no syncope, no chest pain. O: HR 78, BP 132/78. ECG: AF with controlled ventricular response. A: AF, stable. CHA2DS2-VASc score 4 (age, HTN, prior TIA). P: Continue apixaban 5mg BID. Reinforce DOAC adherence. Echo in 6 months.",
    relevance: 0.82,
  },
  "c-004": {
    id: "c-004",
    title: "DOAC Dosing Protocol — Renal Adjustments",
    type: "Protocol",
    source: "Hospital Pharmacy · 2026-04",
    date: "Apr 2026",
    snippet:
      "Apixaban: reduce to 2.5 mg BID if any 2 of: age ≥80, weight ≤60 kg, serum creatinine ≥1.5 mg/dL.",
    body:
      "Apixaban renal dose reduction criteria: reduce to 2.5 mg twice daily if any 2 of the following: age ≥80 years, body weight ≤60 kg, or serum creatinine ≥1.5 mg/dL. Dabigatran: avoid if CrCl <30 mL/min. Rivaroxaban: 15 mg daily if CrCl 15-50 mL/min for AF.",
    relevance: 0.74,
  },
  "c-005": {
    id: "c-005",
    title: "BMP — Vance, E. 2026-06-09",
    type: "Lab Result",
    source: "Core Lab · Order #LAB-19022",
    date: "Jun 9, 2026",
    snippet:
      "Cr 1.1 mg/dL (0.6–1.2). K 4.1. eGFR 62 mL/min/1.73m². Within reference range.",
    body:
      "Basic metabolic panel. Na 139, K 4.1, Cl 102, HCO3 26, BUN 18, Cr 1.1, Glucose 102. eGFR 62 mL/min/1.73m². All values within reference range. No action required.",
    relevance: 0.6,
  },
  "c-006": {
    id: "c-006",
    title: "Heart Failure Outpatient Protocol — GDMT",
    type: "Protocol",
    source: "Cardiology · v3.2",
    date: "Mar 2026",
    snippet:
      "Initiate or up-titrate beta-blocker, ACEi/ARNI, MRA, and SGLT2i as tolerated. Reassess every 2 weeks.",
    body:
      "Guideline-directed medical therapy (GDMT) for HFrEF: titrate to maximum tolerated dose of (1) beta-blocker, (2) ACEi/ARB/ARNI, (3) MRA, (4) SGLT2 inhibitor. Reassess clinically every 2 weeks until target reached. Monitor renal function, potassium, and blood pressure at each visit.",
    relevance: 0.91,
  },
};

export const citationList = Object.values(citations);