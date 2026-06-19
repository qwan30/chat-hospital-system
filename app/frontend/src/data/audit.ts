export interface AuditEvent {
  id: string;
  ts: string;
  user: string;
  role: string;
  action: string;
  target: string;
  result: "success" | "deny" | "pending";
  category: "auth" | "phi" | "ai" | "admin" | "doc";
  ip: string;
  details?: string;
}

const users = [
  ["Dr. Sarah Chen", "Cardiologist"],
  ["Dr. M. Patel", "Cardiologist"],
  ["Nurse R. Owens", "RN"],
  ["Admin J. Kim", "Compliance"],
  ["Dr. L. Garcia", "Hospitalist"],
  ["Records Bot", "System"],
] as const;

const actions: Array<[string, AuditEvent["category"]]> = [
  ["Viewed patient chart", "phi"],
  ["AI query: anticoagulation", "ai"],
  ["AI query: GDMT titration", "ai"],
  ["Document indexed", "doc"],
  ["Access request submitted", "phi"],
  ["Access granted", "phi"],
  ["Access denied", "phi"],
  ["Login (SSO)", "auth"],
  ["MFA verified", "auth"],
  ["Permissions changed", "admin"],
  ["Document upload", "doc"],
  ["Exported audit report", "admin"],
  ["AI refused (insufficient evidence)", "ai"],
];

function rand<T>(arr: readonly T[]) {
  return arr[Math.floor(Math.random() * arr.length)];
}

const targets = [
  "MRN-48201 (Vance, E.)",
  "MRN-48830 (Raman, P.)",
  "MRN-49222 (O'Connor, L.)",
  "Doc d-04 Sepsis-Bundle",
  "Doc d-12 Formulary",
  "Role: Records Staff",
  "Thread t-001",
  "Thread t-003",
];

const seedTs = new Date("2026-06-12T10:00:00Z").getTime();

export const auditEvents: AuditEvent[] = Array.from({ length: 32 }).map((_, i) => {
  const [u, r] = users[i % users.length];
  const [a, c] = actions[i % actions.length];
  const result: AuditEvent["result"] = a.includes("denied")
    ? "deny"
    : a.includes("request")
      ? "pending"
      : "success";
  const ts = new Date(seedTs - i * 1000 * 60 * 7).toISOString();
  return {
    id: `a-${String(i + 1).padStart(3, "0")}`,
    ts,
    user: u,
    role: r,
    action: a,
    target: targets[i % targets.length],
    result,
    category: c,
    ip: `10.${20 + (i % 8)}.${i % 250}.${(i * 7) % 250}`,
    details:
      c === "ai"
        ? "Query routed to RAG pipeline. 3 citations returned. PHI redaction applied."
        : c === "phi"
          ? "RBAC check passed for unit Cardiology · 4N. Justification: clinical consult."
          : c === "doc"
            ? "OCR + embedding completed. 12 chunks added to vector index."
            : "Standard event.",
  };
});
