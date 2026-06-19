export interface AnswerFeedback {
  id: string;
  thread: string;
  user: string;
  rating: "up" | "down";
  reason?: string;
  citationQuality: 1 | 2 | 3 | 4 | 5;
  ts: string;
}

export const feedback: AnswerFeedback[] = [
  {
    id: "f-001",
    thread: "t-001",
    user: "Dr. Sarah Chen",
    rating: "up",
    citationQuality: 5,
    ts: "2026-06-12T16:02:00Z",
  },
  {
    id: "f-002",
    thread: "t-002",
    user: "Dr. L. Garcia",
    rating: "down",
    reason: "Citation didn't actually support claim about beta-blocker dose.",
    citationQuality: 2,
    ts: "2026-06-12T15:30:00Z",
  },
  {
    id: "f-003",
    thread: "t-003",
    user: "Dr. Sarah Chen",
    rating: "up",
    citationQuality: 4,
    ts: "2026-06-12T14:18:00Z",
  },
  {
    id: "f-004",
    thread: "t-004",
    user: "Dr. M. Patel",
    rating: "down",
    reason: "Refused — but the evidence was actually in formulary doc.",
    citationQuality: 3,
    ts: "2026-06-12T13:01:00Z",
  },
  {
    id: "f-005",
    thread: "t-005",
    user: "Nurse R. Owens",
    rating: "up",
    citationQuality: 5,
    ts: "2026-06-12T11:45:00Z",
  },
];
