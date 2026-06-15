export interface PromptTemplate {
  id: string;
  title: string;
  category: "Cardiology" | "Internal Med" | "ICU" | "Discharge" | "Pharmacy";
  body: string;
  usage: number;
}

export const promptTemplates: PromptTemplate[] = [
  { id: "tpl-001", title: "Summarize last 24h of vitals", category: "ICU", body: "Summarize this patient's last 24 hours of vitals (HR, BP, SpO2, RR, T) with trend and any clinically significant deviations. Cite specific timestamps.", usage: 142 },
  { id: "tpl-002", title: "GDMT titration check", category: "Cardiology", body: "Review current heart failure GDMT therapy for this patient. Identify gaps versus guideline-recommended targets and propose next titration steps with evidence.", usage: 98 },
  { id: "tpl-003", title: "Discharge readiness summary", category: "Discharge", body: "Generate a one-page discharge readiness summary covering active problems, pending labs, medication reconciliation, and follow-up needs.", usage: 76 },
  { id: "tpl-004", title: "Anticoagulation review", category: "Cardiology", body: "Review anticoagulation appropriateness for this patient given AFib, renal function, and bleeding risk. Cite CHA2DS2-VASc and HAS-BLED.", usage: 64 },
  { id: "tpl-005", title: "Sepsis bundle compliance", category: "Internal Med", body: "Check sepsis bundle compliance for this encounter (lactate, blood cx, antibiotics within 1h, fluid resuscitation). Cite source orders/results.", usage: 51 },
  { id: "tpl-006", title: "Drug-allergy cross-check", category: "Pharmacy", body: "Cross-check the active medication list against this patient's documented allergies and current renal/hepatic function. Cite the rule source.", usage: 40 },
];