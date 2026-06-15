import type { ChatMessageData } from "@/components/hms/ChatMessage";

export interface ChatThread {
  id: string;
  patientId?: string;
  title: string;
  updated: string;
  messages: ChatMessageData[];
}

export const threads: ChatThread[] = [
  {
    id: "t-001",
    patientId: "p-001",
    title: "AF anticoagulation review — Vance",
    updated: "12 min ago",
    messages: [
      {
        id: "m1",
        role: "user",
        content: "Should Eleanor Vance continue apixaban given her recent labs?",
        time: "09:14",
      },
      {
        id: "m2",
        role: "assistant",
        time: "09:14",
        content:
          "Based on her CHA2DS2-VASc of 4, oral anticoagulation is indicated [1]. Her most recent BMP shows Cr 1.1 mg/dL and eGFR 62 mL/min/1.73m² [3], which does not meet renal dose-reduction criteria [4]. Continuing apixaban 5 mg BID is appropriate [2].",
        citations: [
          { n: 1, sourceId: "c-001" },
          { n: 2, sourceId: "c-003" },
          { n: 3, sourceId: "c-005" },
          { n: 4, sourceId: "c-004" },
        ],
      },
    ],
  },
  {
    id: "t-002",
    patientId: "p-004",
    title: "CHF GDMT optimization — Raman",
    updated: "1h ago",
    messages: [
      {
        id: "m1",
        role: "user",
        content: "What is the next step in GDMT titration for Priya Raman?",
        time: "08:01",
      },
      {
        id: "m2",
        role: "assistant",
        time: "08:02",
        content:
          "Per the HFrEF protocol [1], continue up-titration of beta-blocker and ARNI to maximum tolerated doses, and consider initiating an SGLT2 inhibitor if not already on therapy. Reassess in 2 weeks with renal panel.",
        citations: [{ n: 1, sourceId: "c-006" }],
      },
    ],
  },
  {
    id: "t-003",
    title: "Sepsis bundle protocol question",
    updated: "Yesterday",
    messages: [
      {
        id: "m1",
        role: "user",
        content: "What is the 1-hour sepsis bundle target lactate?",
        time: "16:22",
      },
      {
        id: "m2",
        role: "assistant",
        time: "16:22",
        content:
          "I couldn't locate an indexed protocol that specifies the 1-hour sepsis bundle lactate threshold for this hospital. Please consult the ED protocol binder or upload the latest sepsis bundle policy for indexing.",
      },
    ],
  },
];

export function getThread(id: string) {
  return threads.find((t) => t.id === id);
}

export function getThreadByPatient(patientId: string) {
  return threads.find((t) => t.patientId === patientId);
}