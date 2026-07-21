export type Role =
  | "cardiologist"
  | "hospitalist"
  | "rn"
  | "pharmacist"
  | "front_desk"
  | "admin"
  | "security";

export const ROLES: { id: Role; label: string; description: string }[] = [
  {
    id: "cardiologist",
    label: "Cardiologist",
    description: "Cardiology unit · full clinical access",
  },
  {
    id: "hospitalist",
    label: "Hospitalist",
    description: "Assigned patients · cross-unit consult",
  },
  { id: "rn", label: "Registered Nurse", description: "Bedside · assigned patients" },
  { id: "pharmacist", label: "Pharmacist", description: "Meds + labs · review queue" },
  { id: "front_desk", label: "Front Desk", description: "Demographics + access requests" },
  { id: "admin", label: "Admin", description: "Workspace-wide · full system access" },
  { id: "security", label: "Security Auditor", description: "Audit trail + compliance logs" },
];

export const ROLE_LABEL: Record<Role, string> = {
  cardiologist: "Cardiologist",
  hospitalist: "Hospitalist",
  rn: "Registered Nurse",
  pharmacist: "Pharmacist",
  front_desk: "Front Desk",
  admin: "Admin",
  security: "Security Auditor",
};

export const ROLE_TONE: Record<Role, string> = {
  cardiologist: "bg-primary/10 text-primary border-primary/20",
  hospitalist: "bg-info/10 text-info border-info/20",
  rn: "bg-success/10 text-success border-success/20",
  pharmacist: "bg-ai/10 text-ai border-ai/20",
  front_desk: "bg-warning/10 text-warning border-warning/20",
  admin: "bg-destructive/10 text-destructive border-destructive/20",
  security: "bg-amber-500/10 text-amber-500 border-amber-500/20",
};

/** Routes only Admin may access (prefix match). */
const ADMIN_ONLY = [
  "/admin",
  "/access-policy",
  "/integrations",
  "/metrics",
  "/screens",
  "/settings",
  "/audit/compliance-summary",
  "/audit/export",
  "/audit/denied",
];

/** Routes Admin + the listed roles may access. */
const ROLE_ROUTES: Array<{ prefix: string; roles: Role[] }> = [
  { prefix: "/pharmacy", roles: ["pharmacist"] },
  { prefix: "/medication-conflicts", roles: ["pharmacist"] },
  { prefix: "/graph", roles: ["cardiologist", "hospitalist"] },
  { prefix: "/citations", roles: ["cardiologist", "hospitalist", "pharmacist"] },
  { prefix: "/timeline", roles: ["cardiologist", "hospitalist", "rn"] },
  { prefix: "/chat", roles: ["cardiologist", "hospitalist", "rn", "pharmacist"] },
  { prefix: "/documents", roles: ["cardiologist", "hospitalist", "rn", "pharmacist"] },
  {
    prefix: "/access-requests",
    roles: ["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk"],
  },
  { prefix: "/patients", roles: ["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk"] },
  {
    prefix: "/dashboard",
    roles: ["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk", "security"],
  },
  {
    prefix: "/notifications",
    roles: ["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk"],
  },
  {
    prefix: "/settings",
    roles: ["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk", "security"],
  },
  {
    prefix: "/help",
    roles: ["cardiologist", "hospitalist", "rn", "pharmacist", "front_desk", "security"],
  },
  { prefix: "/audit", roles: ["admin", "security"] },
];

/** Patient sub-tabs visible to each role. */
export const PATIENT_TABS: Record<Role, string[]> = {
  cardiologist: [
    "overview",
    "timeline",
    "labs",
    "medications",
    "documents",
    "access-history",
    "medication-review",
  ],
  hospitalist: ["overview", "timeline", "labs", "medications", "documents", "medication-review"],
  rn: ["overview", "timeline", "medications", "documents"],
  pharmacist: ["overview", "medications", "medication-review", "documents", "labs"],
  front_desk: ["overview"],
  security: ["overview"],
  admin: [
    "overview",
    "timeline",
    "labs",
    "medications",
    "documents",
    "access-history",
    "medication-review",
  ],
};

/** Sidebar landing per role. */
export function landingFor(role: Role): string {
  switch (role) {
    case "pharmacist":
      return "/pharmacy/review-queue";
    case "rn":
      return "/patients";
    case "front_desk":
      return "/patients";
    case "security":
      return "/audit";
    case "admin":
      return "/dashboard";
    default:
      return "/dashboard";
  }
}

/** Always-allowed paths regardless of role (auth/error screens etc.). */
const PUBLIC_APP_PATHS = ["/error/", "/help/"];

export function canAccess(role: Role | null | undefined, pathname: string): boolean {
  if (!role) return false;
  if (role === "admin") return true;
  if (PUBLIC_APP_PATHS.some((p) => pathname.startsWith(p))) return true;

  // Admin-only routes
  if (ADMIN_ONLY.some((p) => pathname === p || pathname.startsWith(p + "/"))) {
    return false;
  }

  // Per-role allow list
  for (const entry of ROLE_ROUTES) {
    if (pathname === entry.prefix || pathname.startsWith(entry.prefix + "/")) {
      return entry.roles.includes(role);
    }
  }
  // Default deny for unknown paths
  return false;
}

export function canAccessPatientTab(role: Role, tab: string): boolean {
  return PATIENT_TABS[role]?.includes(tab) ?? false;
}

export function canCreatePatient(role: Role): boolean {
  return role === "front_desk";
}

/** First patient sub-tab a role can see — used to redirect away from forbidden tabs. */
export function firstAllowedPatientTab(role: Role): string {
  return PATIENT_TABS[role]?.[0] ?? "overview";
}

/** Classify why a path is forbidden, for friendlier error messaging. */
export function forbiddenReason(role: Role, pathname: string): "role" | "workspace-scope" {
  // Patient deep-link to another workspace — flag as scope rather than role.
  if (/^\/patients\/[^/]+/.test(pathname)) return "workspace-scope";
  if (/^\/graph\/patients\/[^/]+/.test(pathname)) return "workspace-scope";
  void role;
  return "role";
}
