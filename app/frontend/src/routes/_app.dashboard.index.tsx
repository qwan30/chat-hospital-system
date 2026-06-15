import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/hms/StatusBadge";
import {
  ArrowRight,
  Clock,
  FileCheck2,
  MessageSquare,
  Quote,
  Search,
  Sparkles,
  Upload,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { dailyQueries, lookupTimeTrend, sparkCited, sparkDocs, sparkLatency, sparkQueries } from "@/data/metrics";
import { patients } from "@/data/patients";
import { threads } from "@/data/threads";
import { documents } from "@/data/documents";

export const Route = createFileRoute("/_app/dashboard/")({
  head: () => ({
    meta: [
      { title: "Dashboard — HMS AI Copilot" },
      { name: "description", content: "Operational overview of the HMS AI Copilot workspace." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const recent = patients.slice(0, 5);
  return (
    <AppShell>
      <PageHeader
        title="Good morning, Dr. Sarah Chen"
        description="Here's what's happening across the cardiology service today."
      />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Avg summary time" value="2m 18s" icon={Clock} tone="primary" delta={{ value: "−12s", positive: true }} spark={sparkLatency} />
        <MetricCard label="Cited answers" value="94.6%" icon={Quote} tone="citation" delta={{ value: "+1.2%", positive: true }} spark={sparkCited} />
        <MetricCard label="Authorized queries" value="218" icon={Sparkles} tone="ai" delta={{ value: "+18", positive: true }} spark={sparkQueries} />
        <MetricCard label="Indexed documents" value="12,842" icon={FileCheck2} tone="secondary" delta={{ value: "+142", positive: true }} spark={sparkDocs} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold">Find a patient or start a task</h3>
              <p className="text-xs text-muted-foreground">
                Search by MRN, name, or ask the assistant anything.
              </p>
            </div>
          </div>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="MRN / patient name / question..." className="pl-8" />
            </div>
            <Button asChild>
              <Link to="/chat"><Sparkles className="mr-1 h-4 w-4" /> Ask</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/documents"><Upload className="mr-1 h-4 w-4" /> Upload</Link>
            </Button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {["Summarize last admission", "Active medications", "Pending labs", "Care gaps"].map(
              (s) => (
                <button
                  key={s}
                  className="rounded-full border bg-muted/40 px-3 py-1 text-xs hover:bg-muted"
                >
                  {s}
                </button>
              ),
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Recent threads</h3>
            <Link to="/chat" className="text-xs font-medium text-primary hover:underline">
              View all
            </Link>
          </div>
          <ul className="mt-3 space-y-1">
            {threads.slice(0, 4).map((t) => (
              <li key={t.id}>
                <Link
                  to={t.patientId ? "/chat/patients/$patientId" : "/chat"}
                  params={t.patientId ? { patientId: t.patientId } : undefined}
                  className="flex items-start gap-2 rounded-md p-2 hover:bg-muted"
                >
                  <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-ai" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{t.title}</p>
                    <p className="text-xs text-muted-foreground">{t.updated}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="overflow-hidden p-0 lg:col-span-2">
          <div className="flex items-center justify-between border-b p-5">
            <h3 className="text-sm font-semibold">Recent patients</h3>
            <Link to="/patients" className="inline-flex items-center text-xs font-medium text-primary hover:underline">
              All patients <ArrowRight className="ml-0.5 h-3 w-3" />
            </Link>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient</TableHead>
                <TableHead>MRN</TableHead>
                <TableHead>Condition</TableHead>
                <TableHead>Last visit</TableHead>
                <TableHead>Access</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recent.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">
                    <Link
                      to={p.access === "allow" ? "/chat/patients/$patientId" : "/patients/$id/access-denied"}
                      params={p.access === "allow" ? { patientId: p.id } : { id: p.id }}
                      className="hover:underline"
                    >
                      {p.name}
                    </Link>
                    <div className="text-xs text-muted-foreground">{p.age} · {p.sex} · {p.unit}</div>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{p.mrn}</TableCell>
                  <TableCell className="text-sm">{p.condition}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{p.lastVisit}</TableCell>
                  <TableCell><StatusBadge status={p.access} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Document processing</h3>
            <Link to="/documents" className="text-xs font-medium text-primary hover:underline">
              Manage
            </Link>
          </div>
          <ul className="mt-3 space-y-2">
            {documents.slice(0, 5).map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-2 rounded-md border p-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{d.name}</p>
                  <p className="text-xs text-muted-foreground">{d.category} · {d.size}</p>
                </div>
                <StatusBadge status={d.status} />
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="text-sm font-semibold">Lookup time — manual vs. copilot (minutes)</h3>
          <div className="mt-4 h-64">
            <ResponsiveContainer>
              <LineChart data={lookupTimeTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="w" stroke="var(--color-muted-foreground)" fontSize={12} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={12} />
                <Tooltip contentStyle={{ background: "var(--color-card)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="manual" stroke="var(--color-chart-5)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="copilot" stroke="var(--color-chart-1)" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card className="p-5">
          <h3 className="text-sm font-semibold">Query volume — last 7 days</h3>
          <div className="mt-4 h-64">
            <ResponsiveContainer>
              <BarChart data={dailyQueries}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="d" stroke="var(--color-muted-foreground)" fontSize={12} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={12} />
                <Tooltip contentStyle={{ background: "var(--color-card)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="queries" fill="var(--color-chart-1)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="refused" fill="var(--color-chart-3)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}