import { createFileRoute, Link } from "@tanstack/react-router";
import { RouteError } from "@/components/hms/RouteError";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/hms/StatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { getAuditLogs, type AuditLog } from "@/lib/api/audit";
import { Download, Filter, Search } from "lucide-react";
import { useState } from "react";
import { formatDateTime } from "@/lib/format";
import { useQuery } from "@tanstack/react-query";

export const Route = createFileRoute("/_app/audit/")({
  head: () => ({
    meta: [{ title: "Audit logs — HMS AI Copilot" }],
  }),
  component: AuditPage,
  errorComponent: RouteError,
});

const categoryColor: Record<string, string> = {
  auth: "bg-info/10 text-info",
  phi: "bg-destructive/10 text-destructive",
  ai: "bg-ai/10 text-ai",
  admin: "bg-primary/10 text-primary",
  doc: "bg-secondary/10 text-secondary",
};

function AuditPage() {
  const [selected, setSelected] = useState<AuditLog | null>(null);

  const {
    data: auditResponse,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => getAuditLogs(),
  });

  const auditEvents = auditResponse?.items || [];

  return (
    <AppShell>
      <PageHeader
        title="Audit logs"
        description="Tamper-evident event stream for all PHI, AI, and admin actions."
        actions={
          <>
            <Button variant="outline" size="sm">
              <Download className="mr-1 h-4 w-4" /> Export
            </Button>
            <Button size="sm">View signed digest</Button>
          </>
        }
        chips={
          <>
            <Badge variant="secondary">{auditEvents.length} events</Badge>
            <Badge variant="secondary" className="bg-success/10 text-success">
              {auditEvents.filter((e) => e.outcome === "allowed" || e.outcome === "success").length}{" "}
              success
            </Badge>
            <Badge variant="secondary" className="bg-destructive/10 text-destructive">
              {auditEvents.filter((e) => e.outcome === "denied" || e.outcome === "deny").length}{" "}
              denied
            </Badge>
          </>
        }
      />

      <Card className="overflow-hidden p-0">
        <div className="flex flex-wrap items-center gap-2 border-b p-3">
          <div className="relative flex-1 max-w-md">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Search by user, action, or resource..." className="h-9 pl-8" />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="mr-1 h-4 w-4" /> Filter
          </Button>
          <Button variant="ghost" size="sm">
            Last 24h
          </Button>
          <Button variant="ghost" size="sm">
            PHI only
          </Button>
          <Button variant="ghost" size="sm">
            AI only
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Result</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Loading audit logs...
                </TableCell>
              </TableRow>
            ) : isError ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-destructive">
                  Failed to load audit logs. Please try again later.
                </TableCell>
              </TableRow>
            ) : (
              auditEvents.map((e) => (
                <Sheet key={e.id}>
                  <SheetTrigger asChild>
                    <TableRow onClick={() => setSelected(e)} className="cursor-pointer">
                      <TableCell className="font-mono text-xs">
                        {formatDateTime(e.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm font-medium">{e.user_id}</div>
                      </TableCell>
                      <TableCell className="text-sm">{e.action}</TableCell>
                      <TableCell className="text-sm">{e.resource_id}</TableCell>
                      <TableCell>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize bg-secondary/10 text-secondary`}
                        >
                          {e.resource_type}
                        </span>
                      </TableCell>
                      <TableCell>
                        <StatusBadge
                          status={
                            e.outcome === "allowed" || e.outcome === "success"
                              ? "success"
                              : e.outcome === "denied" || e.outcome === "deny"
                                ? "deny"
                                : "pending"
                          }
                        />
                      </TableCell>
                    </TableRow>
                  </SheetTrigger>
                  <SheetContent className="w-[420px] sm:max-w-[420px]">
                    <SheetHeader>
                      <SheetTitle>Event {e.id}</SheetTitle>
                      <SheetDescription>{e.action}</SheetDescription>
                    </SheetHeader>
                    <div className="mt-5 space-y-4 text-sm">
                      <Field k="Timestamp" v={formatDateTime(e.created_at)} />
                      <Field k="User" v={`${e.user_id}`} />
                      <Field k="Target" v={e.resource_id} />
                      <Field k="Category" v={e.resource_type} />
                      <Field k="Result" v={e.outcome} />
                      <Field k="Reason" v={e.reason || "N/A"} />
                      <div>
                        <div className="text-xs uppercase tracking-wider text-muted-foreground">
                          Details
                        </div>
                        <p className="mt-1 rounded-md border bg-muted/40 p-3 text-sm leading-relaxed">
                          {e.action}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Link
                          to={`/audit/${e.id}/raw` as any}
                          className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
                        >
                          View raw JSON
                        </Link>
                        <Link
                          to={"/audit/traces/tr-001" as any}
                          className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
                        >
                          Open trace
                        </Link>
                      </div>
                      <div className="rounded-md border border-success/30 bg-success/5 p-3 text-xs">
                        <span className="font-semibold text-success">Tamper-evident</span> · this
                        event is cryptographically chained to the audit ledger.
                      </div>
                    </div>
                  </SheetContent>
                </Sheet>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
      <div className="sr-only">{selected?.id}</div>
    </AppShell>
  );
}

function Field({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-muted-foreground">{k}</div>
      <div className="mt-0.5 font-medium">{v}</div>
    </div>
  );
}
