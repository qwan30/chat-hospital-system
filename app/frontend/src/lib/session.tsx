import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Role } from "@/lib/rbac";
import { mockUsers, type MockUser } from "@/data/mockUsers";
import { getWorkspace, type Workspace } from "@/data/workspaces";
import { useAuth } from "@/lib/auth-context";
import { persistToken, clearToken } from "@/lib/api-client";

const STORAGE_KEY = "hms.session";

export interface Session {
  user: MockUser;
  role: Role;
  workspace: Workspace;
  /** True when authenticated via real JWT backend. */
  isRealAuth: boolean;
  /** The JWT token (only set when isRealAuth is true). */
  token?: string | null;
}

interface SessionContextValue {
  session: Session | null;
  hydrated: boolean;
  signIn: (role: Role, workspaceId?: string) => void;
  signOut: () => void;
  switchRole: (role: Role) => void;
  switchWorkspace: (workspaceId: string) => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

function buildSession(
  role: Role,
  workspaceId?: string,
  isRealAuth = false,
  token?: string | null,
): Session {
  const user = mockUsers[role];
  const wsId =
    workspaceId && user.availableWorkspaceIds.includes(workspaceId)
      ? workspaceId
      : user.defaultWorkspaceId;
  const workspace = getWorkspace(wsId)!;

  let assignedToken = token;
  if (!isRealAuth && !assignedToken) {
    if (role === "admin") assignedToken = "dev-admin";
    else if (role === "pharmacist") assignedToken = "dev-pharmacist";
    else if (role === "rn") assignedToken = "dev-nurse";
    else if (role === "front_desk")
      assignedToken = "dev-records"; // Fallback to records
    else assignedToken = "dev-doctor";
  }

  return { user, role, workspace, isRealAuth, token: assignedToken };
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const { authUser, token, hydrated: authHydrated } = useAuth();
  const [session, setSession] = useState<Session | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (session?.token) {
      persistToken(session.token);
    } else {
      clearToken();
    }
  }, [session]);

  // Sync with AuthProvider: if JWT user exists, map role to our Role type.
  // Otherwise fall back to localStorage mock session.
  useEffect(() => {
    if (!authHydrated) return;

    if (authUser && token) {
      const role = mapBackendRole(authUser.role);
      const s = buildSession(role, undefined, true, token);
      setSession(s);
    } else {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw) as { role: Role; workspaceId: string };
          if (parsed?.role && mockUsers[parsed.role]) {
            setSession(buildSession(parsed.role, parsed.workspaceId));
          }
        }
      } catch {
        /* ignore */
      }
    }
    setHydrated(true);
  }, [authHydrated, authUser, token]);

  const persist = (s: Session | null) => {
    if (typeof window === "undefined") return;
    if (s) {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ role: s.role, workspaceId: s.workspace.id }),
      );
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const signIn = useCallback((role: Role, workspaceId?: string) => {
    const s = buildSession(role, workspaceId);
    setSession(s);
    persist(s);
  }, []);

  const signOut = useCallback(() => {
    setSession(null);
    persist(null);
  }, []);

  const switchRole = useCallback((role: Role) => {
    const s = buildSession(role);
    setSession(s);
    persist(s);
  }, []);

  const switchWorkspace = useCallback((workspaceId: string) => {
    setSession((prev) => {
      if (!prev) return prev;
      const next = buildSession(prev.role, workspaceId, prev.isRealAuth, prev.token);
      persist(next);
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ session, hydrated, signIn, signOut, switchRole, switchWorkspace }),
    [session, hydrated, signIn, signOut, switchRole, switchWorkspace],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}

function mapBackendRole(backendRole: string): Role {
  const lower = backendRole.toLowerCase();
  if (lower.includes("admin")) return "admin";
  if (lower.includes("pharmac")) return "pharmacist";
  if (lower.includes("nurse") || lower === "rn") return "rn";
  if (lower.includes("hospital")) return "hospitalist";
  if (lower.includes("front") || lower.includes("desk")) return "front_desk";
  return "cardiologist";
}
