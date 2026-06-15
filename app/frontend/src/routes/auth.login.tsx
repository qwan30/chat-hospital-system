import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AuthSplitLayout } from "@/components/shell/AuthSplitLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ShieldCheck, KeySquare, Activity } from "lucide-react";
import { useState, type FormEvent } from "react";
import { ROLES, type Role, landingFor } from "@/lib/rbac";
import { mockUsers } from "@/data/mockUsers";
import { workspaces } from "@/data/workspaces";
import { useSession } from "@/lib/session";
import { useAuth } from "@/lib/auth-context";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/auth/login")({
  head: () => ({
    meta: [
      { title: "Sign in — HMS AI Copilot" },
      { name: "description", content: "Secure staff sign-in for HMS AI Copilot." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { signIn } = useSession();
  const { login, loading: authLoading, error: authError } = useAuth();

  // Real login state
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // Mock login state
  const [mockLoading, setMockLoading] = useState(false);
  const [role, setRole] = useState<Role>("cardiologist");
  const user = mockUsers[role];
  const [workspaceId, setWorkspaceId] = useState<string>(user.defaultWorkspaceId);
  const availableWs = workspaces.filter((w) => user.availableWorkspaceIds.includes(w.id));

  const effectiveWorkspaceId = user.availableWorkspaceIds.includes(workspaceId)
    ? workspaceId
    : user.defaultWorkspaceId;

  const handleRole = (r: Role) => {
    setRole(r);
    setWorkspaceId(mockUsers[r].defaultWorkspaceId);
  };

  const handleRealLogin = async (e: FormEvent) => {
    e.preventDefault();
    const ok = await login(username, password);
    if (ok) {
      navigate({ to: "/dashboard" });
    }
  };

  const handleMockSignIn = () => {
    signIn(role, effectiveWorkspaceId);
    setMockLoading(true);
    setTimeout(() => navigate({ to: landingFor(role) }), 300);
  };

  const submitMock = (e: FormEvent) => {
    e.preventDefault();
    handleMockSignIn();
  };

  return (
    <AuthSplitLayout>
      <div>
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Welcome back</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Sign in with your credentials or select a demo role.
          </p>
        </div>

        <Tabs defaultValue="real" className="mt-6">
          <TabsList className="w-full">
            <TabsTrigger value="real" className="flex-1">
              Real Login
            </TabsTrigger>
            <TabsTrigger value="mock" className="flex-1">
              Demo Role
            </TabsTrigger>
          </TabsList>

          <TabsContent value="real">
            <form className="space-y-4" onSubmit={handleRealLogin}>
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="your_username"
                  required
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Link to="/auth/forgot-password" className="text-xs text-primary hover:underline">
                    Forgot?
                  </Link>
                </div>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>
              {authError && <p className="text-sm text-destructive">{authError}</p>}
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Checkbox defaultChecked /> Remember this device for 30 days
              </label>
              <Button className="w-full" type="submit" disabled={authLoading}>
                {authLoading ? "Signing in..." : "Sign in"}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="mock">
            <Button
              variant="outline"
              className="mb-5 w-full justify-center gap-2"
              onClick={handleMockSignIn}
            >
              <KeySquare className="h-4 w-4" /> Sign in with Hospital SSO
            </Button>
            <div className="mb-5 flex items-center gap-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs uppercase tracking-wider text-muted-foreground">
                or select role
              </span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <form className="space-y-4" onSubmit={submitMock}>
              <div className="space-y-2">
                <Label>Role</Label>
                <div className="grid grid-cols-2 gap-2">
                  {ROLES.map((r) => (
                    <button
                      type="button"
                      key={r.id}
                      onClick={() => handleRole(r.id)}
                      className={cn(
                        "rounded-lg border p-2 text-left text-xs transition",
                        role === r.id
                          ? "border-primary bg-primary/10 text-primary"
                          : "hover:bg-muted/50",
                      )}
                    >
                      <div className="font-semibold">{r.label}</div>
                      <div className="mt-0.5 text-[10px] opacity-80">{r.description}</div>
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="workspace">Workspace</Label>
                <Select key={role} value={effectiveWorkspaceId} onValueChange={setWorkspaceId}>
                  <SelectTrigger id="workspace">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableWs.map((w) => (
                      <SelectItem key={w.id} value={w.id}>
                        {w.name} · {w.department}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={user.email} readOnly />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mock-password">Password</Label>
                <Input id="mock-password" type="password" defaultValue="••••••••" required />
              </div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Checkbox defaultChecked /> Remember this device for 30 days
              </label>
              <Button className="w-full" disabled={mockLoading}>
                {mockLoading ? "Signing in..." : "Sign in"}
              </Button>
            </form>
          </TabsContent>
        </Tabs>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-success" /> PHI Protection
          </span>
          <span className="inline-flex items-center gap-1">
            <Activity className="h-3 w-3 text-info" /> Audit Logged
          </span>
          <span className="inline-flex items-center gap-1">
            <KeySquare className="h-3 w-3 text-ai" /> RBAC
          </span>
        </div>
      </div>
    </AuthSplitLayout>
  );
}
