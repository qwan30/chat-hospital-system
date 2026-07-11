import { createFileRoute, Link } from "@tanstack/react-router";
import { RouteError } from "@/components/hms/RouteError";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/hms/StatusBadge";
import { AccessRequestDialog } from "@/components/hms/AccessRequestDialog";
import { Bell, Bookmark, Filter, Lock, MessageSquare, Search } from "lucide-react";
import { searchPatients } from "@/lib/api/patients";
import { useState, useEffect } from "react";
import { useSession } from "@/lib/session";
import { useQuery, keepPreviousData } from "@tanstack/react-query";

export const Route = createFileRoute("/_app/patients/")({
  head: () => ({
    meta: [
      { title: "Patients — HMS AI Copilot" },
      { name: "description", content: "Permission-aware patient roster." },
    ],
  }),
  component: PatientsPage,
  errorComponent: RouteError,
});

const statusToneClass: Record<string, string> = {
  stable: "bg-success/10 text-success border-success/20",
  active: "bg-success/10 text-success border-success/20",
  watch: "bg-warning/10 text-warning border-warning/20",
  critical: "bg-destructive/10 text-destructive border-destructive/20",
};

function calculateAge(dob: string | null): number | string {
  if (!dob) return "--";
  const birthDate = new Date(dob);
  const diffMs = Date.now() - birthDate.getTime();
  const ageDt = new Date(diffMs);
  return Math.abs(ageDt.getUTCFullYear() - 1970);
}

function PatientsPage() {
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const { session } = useSession();

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  const {
    data: searchResponse,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["patients", debouncedQ],
    queryFn: () => searchPatients(debouncedQ || undefined, 50),
    placeholderData: keepPreviousData,
  });

  const filtered = searchResponse?.items || [];

  return (
    <AppShell
      rightRail={
        <div className="space-y-4">
          <Card className="p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <Bookmark className="h-4 w-4 text-primary" /> Saved filters
            </div>
            <ul className="space-y-1 text-sm">
              {[
                "My cardiology panel",
                "ICU watch list",
                "Pending access requests",
                "Discharged this week",
              ].map((f) => (
                <li key={f}>
                  <button className="w-full rounded-md p-2 text-left hover:bg-muted">{f}</button>
                </li>
              ))}
            </ul>
          </Card>
          <Card className="p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <Bell className="h-4 w-4 text-warning" /> Alerts
            </div>
            <ul className="space-y-2 text-sm">
              <li className="rounded-md border border-destructive/20 bg-destructive/5 p-2">
                <p className="font-medium text-destructive">Raman, P. — BP 162/98</p>
                <p className="text-xs text-muted-foreground">3 min ago · Cardiology · 4N</p>
              </li>
              <li className="rounded-md border border-warning/20 bg-warning/5 p-2">
                <p className="font-medium">Petersen, N. — Lactate 4.1</p>
                <p className="text-xs text-muted-foreground">22 min ago · ICU · 2W</p>
              </li>
              <li className="rounded-md border p-2">
                <p className="font-medium">3 pending access requests</p>
                <p className="text-xs text-muted-foreground">Awaiting your review</p>
              </li>
            </ul>
          </Card>
        </div>
      }
    >
      <PageHeader
        title="Patients"
        description="Permission-aware roster. Unauthorized records are gated."
        chips={
          <>
            <Badge variant="secondary">
              {filtered.length} in {session?.workspace.name ?? "workspace"}
            </Badge>
            <Badge variant="secondary" className="bg-success/10 text-success">
              {filtered.length} accessible
            </Badge>
          </>
        }
        actions={
          <>
            <Button variant="outline" size="sm">
              <Filter className="mr-1 h-4 w-4" /> Filter
            </Button>
            <Button size="sm">Add patient</Button>
          </>
        }
      />
      <Card className="overflow-hidden p-0">
        <div className="flex items-center gap-2 border-b p-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search by name, MRN..."
              className="h-9 pl-8"
            />
          </div>
          <span className="text-xs text-muted-foreground">{filtered.length} results</span>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Patient</TableHead>
              <TableHead>MRN</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Access</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Loading patients...
                </TableCell>
              </TableRow>
            ) : isError ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-destructive">
                  Failed to load patients. Please try again.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((p) => (
                <TableRow key={p.id}>
                  <TableCell>
                    <div className="font-medium">{p.full_name}</div>
                    <div className="text-xs text-muted-foreground">{calculateAge(p.dob)}</div>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{p.mrn}</TableCell>
                  <TableCell className="text-sm">{p.department || "--"}</TableCell>
                  <TableCell>
                    <span
                      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${statusToneClass[p.status] || "bg-secondary/10 text-secondary"}`}
                    >
                      {p.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status="allow" />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button asChild size="sm" variant="ghost">
                      <Link to="/chat/patients/$patientId" params={{ patientId: p.id }}>
                        <MessageSquare className="mr-1 h-3.5 w-3.5" /> Open chat
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </AppShell>
  );
}
