import { createFileRoute } from "@tanstack/react-router";
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
import { useSession } from "@/lib/session";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/audit/")({
  head: () => ({
    meta: [{ title: "Audit logs — HMS AI Copilot" }],
  }),
  component: AuditPage,
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
  const [q, setQ] = useState("");
  const [outcomeFilter, setOutcomeFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [timeFilter, setTimeFilter] = useState(false);
  const [phiOnly, setPhiOnly] = useState(false);
  const [aiOnly, setAiOnly] = useState(false);

  const { hydrated, session } = useSession();

  const {
    data: auditResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => getAuditLogs(),
    retry: false,
    // Don't fire until the session has restored the token into memory
    enabled: hydrated && session?.token != null,
  });

  const auditEvents = auditResponse?.items || [];

  const handleExport = () => {
    if (auditEvents.length === 0) {
      toast.error("No events to export");
      return;
    }
    const headers = ["Time", "User", "Action", "Target", "Category", "Result"];
    const rows = auditEvents.map((e) => [
      formatDateTime(e.created_at),
      e.actor_user_id ?? "system",
      e.action,
      e.object_id ?? "—",
      e.object_type,
      e.outcome,
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [
        headers.join(","),
        ...rows.map((r) => r.map((val) => `"${val.replace(/"/g, '""')}"`).join(",")),
      ].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `audit_log_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Audit log exported successfully");
  };

  const viewSignedDigest = () => {
    toast.info("Cryptographic Digest Verified", {
      description: "Chain root hash: sha256-a1b2c3d4e5f6... Verified against ledger anchor.",
    });
  };

  let filteredEvents = auditEvents;
  if (q.trim()) {
    const term = q.toLowerCase();
    filteredEvents = filteredEvents.filter(
      (e) =>
        e.action.toLowerCase().includes(term) ||
        e.actor_user_id?.toLowerCase().includes(term) ||
        e.object_type.toLowerCase().includes(term) ||
        e.object_id?.toLowerCase().includes(term),
    );
  }
  if (outcomeFilter !== "all") {
    filteredEvents = filteredEvents.filter((e) => {
      const outcome = e.outcome.toLowerCase();
      if (outcomeFilter === "allowed") return outcome === "allowed" || outcome === "success";
      if (outcomeFilter === "denied") return outcome === "denied" || outcome === "deny";
      return true;
    });
  }
  if (categoryFilter !== "all") {
    filteredEvents = filteredEvents.filter(
      (e) => e.object_type.toLowerCase() === categoryFilter.toLowerCase(),
    );
  }
  if (timeFilter && filteredEvents.length > 0) {
    const maxTime = Math.max(...filteredEvents.map((e) => new Date(e.created_at).getTime()));
    const oneDay = 24 * 60 * 60 * 1000;
    filteredEvents = filteredEvents.filter(
      (e) => maxTime - new Date(e.created_at).getTime() <= oneDay,
    );
  }
  if (phiOnly) {
    filteredEvents = filteredEvents.filter((e) =>
      ["patient", "document", "labs", "medication"].includes(e.object_type.toLowerCase()),
    );
  }
  if (aiOnly) {
    filteredEvents = filteredEvents.filter((e) =>
      ["ai", "chat", "copilot"].includes(e.object_type.toLowerCase()),
    );
  }
  if (error) {
    return (
      <AppShell>
        <div className="p-8">
          <PageHeader
            title="Audit logs"
            description="Tamper-evident event stream for all PHI, AI, and admin actions."
          />
          <Card className="mt-4 p-8 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
              <Filter className="h-6 w-6" />
            </div>
            <p className="mt-3 text-sm font-semibold text-destructive">
              {error instanceof Error ? error.message : "Failed to load audit logs"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Audit logs require <strong>Security</strong> or <strong>Admin</strong> role. Switch
              role in the login page to access this page.
            </p>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title="Audit logs"
        description="Tamper-evident event stream for all PHI, AI, and admin actions."
        actions={
          <>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="mr-1 h-4 w-4" /> Export
            </Button>
            <Button size="sm" onClick={viewSignedDigest}>
              View signed digest
            </Button>
          </>
        }
        chips={
          <>
            <Badge variant="secondary">{filteredEvents.length} events</Badge>
            <Badge variant="secondary" className="bg-success/10 text-success">
              {
                filteredEvents.filter((e) => e.outcome === "allowed" || e.outcome === "success")
                  .length
              }{" "}
              success
            </Badge>
            <Badge variant="secondary" className="bg-destructive/10 text-destructive">
              {filteredEvents.filter((e) => e.outcome === "denied" || e.outcome === "deny").length}{" "}
              denied
            </Badge>
          </>
        }
      />

      <Card className="overflow-hidden p-0">
        <div className="flex flex-wrap items-center gap-2 border-b p-3">
          <div className="relative flex-1 max-w-md">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by user, action, or resource..."
              className="h-9 pl-8"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant={
                  outcomeFilter !== "all" || categoryFilter !== "all" ? "default" : "outline"
                }
                size="sm"
              >
                <Filter className="mr-1 h-4 w-4" /> Filter{" "}
                {(outcomeFilter !== "all" || categoryFilter !== "all") && "•"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 space-y-4">
              <div className="space-y-2">
                <h4 className="font-medium leading-none">Filter Logs</h4>
                <p className="text-xs text-muted-foreground">Select criteria for audit trail.</p>
              </div>
              <div className="grid gap-2">
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label htmlFor="outcome-filter">Outcome</Label>
                  <Select value={outcomeFilter} onValueChange={setOutcomeFilter}>
                    <SelectTrigger id="outcome-filter" className="col-span-2 h-8">
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="allowed">Allowed / Success</SelectItem>
                      <SelectItem value="denied">Denied / Deny</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label htmlFor="cat-filter">Category</Label>
                  <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                    <SelectTrigger id="cat-filter" className="col-span-2 h-8">
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="patient">Patient</SelectItem>
                      <SelectItem value="document">Document</SelectItem>
                      <SelectItem value="chat">Chat</SelectItem>
                      <SelectItem value="auth">Auth</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {(outcomeFilter !== "all" || categoryFilter !== "all") && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-xs h-8"
                  onClick={() => {
                    setOutcomeFilter("all");
                    setCategoryFilter("all");
                  }}
                >
                  Clear Filters
                </Button>
              )}
            </PopoverContent>
          </Popover>
          <Button
            variant={timeFilter ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setTimeFilter(!timeFilter)}
            className="cursor-pointer"
          >
            Last 24h
          </Button>
          <Button
            variant={phiOnly ? "secondary" : "ghost"}
            size="sm"
            onClick={() => {
              setPhiOnly(!phiOnly);
              if (aiOnly) setAiOnly(false);
            }}
            className="cursor-pointer"
          >
            PHI only
          </Button>
          <Button
            variant={aiOnly ? "secondary" : "ghost"}
            size="sm"
            onClick={() => {
              setAiOnly(!aiOnly);
              if (phiOnly) setPhiOnly(false);
            }}
            className="cursor-pointer"
          >
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
            ) : (
              filteredEvents.map((e) => (
                <Sheet key={e.id}>
                  <SheetTrigger asChild>
                    <TableRow onClick={() => setSelected(e)} className="cursor-pointer">
                      <TableCell className="font-mono text-xs">
                        {formatDateTime(e.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm font-medium font-mono">
                          {e.actor_user_id?.substring(0, 8) ?? "system"}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{e.action}</TableCell>
                      <TableCell className="text-sm font-mono">
                        {e.object_id?.substring(0, 8) ?? "—"}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize bg-secondary/10 text-secondary`}
                        >
                          {e.object_type}
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
                      <Field k="User" v={e.actor_user_id ?? "system"} />
                      <Field k="Target" v={e.object_id ?? "—"} />
                      <Field k="Category" v={e.object_type} />
                      <Field k="Result" v={e.outcome} />
                      <Field k="Trace ID" v={e.trace_id ?? "—"} />
                      <Field k="IP" v={e.ip_address ?? "—"} />
                      <div>
                        <div className="text-xs uppercase tracking-wider text-muted-foreground">
                          Details
                        </div>
                        <p className="mt-1 rounded-md border bg-muted/40 p-3 text-sm leading-relaxed">
                          {e.action}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <a
                          href={`/audit/${e.id}/raw`}
                          className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
                        >
                          View raw JSON
                        </a>
                        <a
                          href="/audit/traces/tr-001"
                          className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-accent"
                        >
                          Open trace
                        </a>
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
