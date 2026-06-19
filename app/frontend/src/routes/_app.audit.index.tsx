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
import { auditEvents, type AuditEvent } from "@/data/audit";
import { Download, Filter, Search } from "lucide-react";
import { useState } from "react";
import { formatDateTime } from "@/lib/format";

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
  const [selected, setSelected] = useState<AuditEvent | null>(null);
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
              {auditEvents.filter((e) => e.result === "success").length} success
            </Badge>
            <Badge variant="secondary" className="bg-destructive/10 text-destructive">
              {auditEvents.filter((e) => e.result === "deny").length} denied
            </Badge>
            <Badge variant="secondary" className="bg-warning/10 text-warning">
              {auditEvents.filter((e) => e.result === "pending").length} pending
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
              <TableHead>IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {auditEvents.map((e) => (
              <Sheet key={e.id}>
                <SheetTrigger asChild>
                  <TableRow onClick={() => setSelected(e)} className="cursor-pointer">
                    <TableCell className="font-mono text-xs">{formatDateTime(e.ts)}</TableCell>
                    <TableCell>
                      <div className="text-sm font-medium">{e.user}</div>
                      <div className="text-xs text-muted-foreground">{e.role}</div>
                    </TableCell>
                    <TableCell className="text-sm">{e.action}</TableCell>
                    <TableCell className="text-sm">{e.target}</TableCell>
                    <TableCell>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${categoryColor[e.category]}`}
                      >
                        {e.category}
                      </span>
                    </TableCell>
                    <TableCell>
                      <StatusBadge
                        status={
                          e.result === "success"
                            ? "success"
                            : e.result === "deny"
                              ? "deny"
                              : "pending"
                        }
                      />
                    </TableCell>
                    <TableCell className="font-mono text-xs">{e.ip}</TableCell>
                  </TableRow>
                </SheetTrigger>
                <SheetContent className="w-[420px] sm:max-w-[420px]">
                  <SheetHeader>
                    <SheetTitle>Event {e.id}</SheetTitle>
                    <SheetDescription>{e.action}</SheetDescription>
                  </SheetHeader>
                  <div className="mt-5 space-y-4 text-sm">
                    <Field k="Timestamp" v={formatDateTime(e.ts)} />
                    <Field k="User" v={`${e.user} (${e.role})`} />
                    <Field k="Target" v={e.target} />
                    <Field k="Category" v={e.category} />
                    <Field k="Result" v={e.result} />
                    <Field k="IP address" v={e.ip} />
                    <div>
                      <div className="text-xs uppercase tracking-wider text-muted-foreground">
                        Details
                      </div>
                      <p className="mt-1 rounded-md border bg-muted/40 p-3 text-sm leading-relaxed">
                        {e.details}
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
            ))}
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
