import type { Role } from "@/lib/rbac";

export interface MockUser {
  role: Role;
  name: string;
  email: string;
  initials: string;
  title: string;
  defaultWorkspaceId: string;
  availableWorkspaceIds: string[];
}

export const mockUsers: Record<Role, MockUser> = {
  cardiologist: {
    role: "cardiologist",
    name: "Dr. Sarah Chen",
    email: "s.chen@hospital.org",
    initials: "SC",
    title: "Cardiology · Attending",
    defaultWorkspaceId: "ws-cardio-4n",
    availableWorkspaceIds: ["ws-cardio-4n", "ws-icu-2w"],
  },
  hospitalist: {
    role: "hospitalist",
    name: "Dr. Luis Garcia",
    email: "l.garcia@hospital.org",
    initials: "LG",
    title: "Internal Medicine · Hospitalist",
    defaultWorkspaceId: "ws-onco-7n",
    availableWorkspaceIds: ["ws-onco-7n", "ws-cardio-4n", "ws-icu-2w"],
  },
  rn: {
    role: "rn",
    name: "RN Jamie Owens",
    email: "j.owens@hospital.org",
    initials: "JO",
    title: "ICU · Bedside RN",
    defaultWorkspaceId: "ws-icu-2w",
    availableWorkspaceIds: ["ws-icu-2w", "ws-cardio-4n"],
  },
  pharmacist: {
    role: "pharmacist",
    name: "Pharm. Riya Patel",
    email: "r.patel@hospital.org",
    initials: "RP",
    title: "Inpatient Pharmacy",
    defaultWorkspaceId: "ws-pharmacy",
    availableWorkspaceIds: ["ws-pharmacy"],
  },
  front_desk: {
    role: "front_desk",
    name: "Maria Lopez",
    email: "m.lopez@hospital.org",
    initials: "ML",
    title: "ER · Front Desk",
    defaultWorkspaceId: "ws-er-front",
    availableWorkspaceIds: ["ws-er-front"],
  },
  admin: {
    role: "admin",
    name: "Admin J. Kim",
    email: "j.kim@hospital.org",
    initials: "JK",
    title: "Workspace Admin",
    defaultWorkspaceId: "ws-hospital",
    availableWorkspaceIds: [
      "ws-hospital",
      "ws-cardio-4n",
      "ws-icu-2w",
      "ws-onco-7n",
      "ws-pharmacy",
      "ws-er-front",
    ],
  },
};
