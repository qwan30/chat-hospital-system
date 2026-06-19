import { createFileRoute, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSession } from "@/lib/session";
import { useOnlineStatus } from "@/hooks/use-online-status";
import { getRecentLogs, subscribeLogs, type LogEntry } from "@/lib/log";
import { ROLE_LABEL } from "@/lib/rbac";

export const Route = createFileRoute("/_app/help/diagnostics")({
  head: () => ({ meta: [{ title: "Diagnostics — HMS AI Copilot" }] }),
  component: DiagnosticsPage,
});

function DiagnosticsPage() {
  const { session } = useSession();
  const online = useOnlineStatus();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [logs, setLogs] = useState<LogEntry[]>(() => getRecentLogs());

  useEffect(() => {
    const unsub = subscribeLogs(() => setLogs(getRecentLogs()));
    return () => {
      unsub();
    };
  }, []);

  const rows: Array<[string, React.ReactNode]> = [
    ["User", session?.user.name ?? "—"],
    ["Role", session ? ROLE_LABEL[session.role] : "—"],
    ["Workspace", session?.workspace.name ?? "—"],
    ["Available workspaces", session?.user.availableWorkspaceIds.join(", ") ?? "—"],
    [
      "Route",
      <code key="r" className="font-mono text-xs">
        {pathname}
      </code>,
    ],
    [
      "Online",
      <Badge
        key="o"
        variant={online ? "secondary" : "destructive"}
        className={online ? "bg-success/10 text-success" : ""}
      >
        {online ? "Yes" : "No"}
      </Badge>,
    ],
    ["User agent", typeof navigator !== "undefined" ? navigator.userAgent : "—"],
    [
      "Viewport",
      typeof window !== "undefined" ? `${window.innerWidth}×${window.innerHeight}` : "—",
    ],
    ["Clock", new Date().toISOString()],
  ];

  return (
    <AppShell>
      <PageHeader
        title="Diagnostics"
        description="Session, environment, and recent error log. Useful for QA across roles and workspaces."
      />
      <Card className="p-0">
        <table className="w-full text-sm">
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k} className="border-b last:border-b-0">
                <td className="w-48 bg-muted/30 px-4 py-2 text-xs font-medium uppercase text-muted-foreground">
                  {k}
                </td>
                <td className="px-4 py-2">{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <h2 className="mt-8 text-sm font-semibold">Recent events ({logs.length})</h2>
      <Card className="mt-2 p-0">
        {logs.length === 0 ? (
          <p className="px-4 py-6 text-sm text-muted-foreground">
            No events recorded this session.
          </p>
        ) : (
          <ul className="divide-y">
            {logs.map((e) => (
              <li key={e.id} className="flex items-start gap-3 px-4 py-2 text-xs">
                <Badge variant="outline" className="font-mono uppercase">
                  {e.level}
                </Badge>
                <span className="font-mono text-muted-foreground">{e.ts.slice(11, 19)}</span>
                <span className="font-medium">{e.code ?? "—"}</span>
                <span className="flex-1 truncate">{e.message}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </AppShell>
  );
}
