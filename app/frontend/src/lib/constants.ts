/** Global UI constants — single source of truth for the app shell. */

export const PRODUCT_NAME = "AI-Powered Hospital Knowledge Assistant";

export const CURRENT_USER = {
  full_name: "Dr. Sarah Chen",
  role: "Physician",
  department: "Cardiology",
};

export const CURRENT_ENVIRONMENT = "Synthetic Data";

export const SAFETY_FOOTER =
  "AI can make mistakes. Verify important information. Learn more";

export const SIDEBAR_FOOTER = {
  auditText: "Audit ready",
  lastLogin: "Last login: May 10, 2025, 8:51 AM",
};

export interface NavItem {
  label: string;
  href: string;
  icon: string;
  roles?: string[];
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { label: "Patients", href: "/patients", icon: "Users" },
  { label: "Chat", href: "/chat", icon: "MessageSquare" },
  { label: "Documents", href: "/documents", icon: "FileText" },
  { label: "Audit Logs", href: "/audit", icon: "ShieldCheck" },
  { label: "Metrics", href: "/metrics", icon: "BarChart3" },
];

export const ENVIRONMENTS = [
  {
    id: "synthetic",
    label: "Synthetic Data",
    description: "Mock patient datasets. Safe for testing.",
    icon: "Database",
    color: "blue" as const,
  },
  {
    id: "sandbox",
    label: "Sandbox",
    description: "Isolated environment for development.",
    icon: "FlaskConical",
    color: "orange" as const,
  },
  {
    id: "training",
    label: "Training Mode",
    description: "De-identified historical charts.",
    icon: "GraduationCap",
    color: "purple" as const,
  },
  {
    id: "production",
    label: "Production Data",
    description: "Live hospital intranet data. Strict ABAC.",
    icon: "Lock",
    color: "red" as const,
  },
];
