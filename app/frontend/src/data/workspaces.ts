export interface Workspace {
  id: string;
  name: string;
  department: string;
  /** Substring matched against patient.unit; undefined = all units */
  scope?: string;
}

export const workspaces: Workspace[] = [
  { id: "ws-cardio-4n", name: "Cardiology 4N", department: "Cardiology", scope: "Cardiology" },
  { id: "ws-icu-2w", name: "ICU 2W", department: "Critical Care", scope: "ICU" },
  { id: "ws-onco-7n", name: "Oncology 7N", department: "Oncology", scope: "Oncology" },
  { id: "ws-pharmacy", name: "Pharmacy Dept", department: "Pharmacy" },
  { id: "ws-er-front", name: "ER Front Desk", department: "Emergency" },
  { id: "ws-hospital", name: "Hospital-wide", department: "Admin" },
];

export function getWorkspace(id: string | null | undefined): Workspace | undefined {
  if (!id) return undefined;
  return workspaces.find((w) => w.id === id);
}
