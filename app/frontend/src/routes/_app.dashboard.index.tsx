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
  AlertTriangle,
  Loader2,
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
// Static data for charts (backend doesn't serve chart series yet)
const dailyQueries = [
  { d: "Mon", queries: 142, refused: 6 },
  { d: "Tue", queries: 168, refused: 9 },
  { d: "Wed", queries: 154, refused: 5 },
  { d: "Thu", queries: 191, refused: 11 },
  { d: "Fri", queries: 218, refused: 8 },
  { d: "Sat", queries: 96, refused: 3 },
  { d: "Sun", queries: 78, refused: 4 },
];
const lookupTimeTrend = [
  { w: "W1", manual: 6.4, copilot: 3.1 },
  { w: "W2", manual: 6.2, copilot: 2.8 },
  { w: "W3", manual: 6.5, copilot: 2.6 },
  { w: "W4", manual: 6.1, copilot: 2.4 },
  { w: "W5", manual: 6.3, copilot: 2.3 },
  { w: "W6", manual: 6.0, copilot: 2.2 },
];
const sparkQueries = [42, 51, 38, 65, 58, 72, 84];
const sparkLatency = [1.2, 1.1, 1.3, 1.0, 0.9, 1.0, 0.95];
const sparkDocs = [12200, 12380, 12510, 12640, 12720, 12800, 12842];
const sparkCited = [91, 92, 93, 92, 94, 94, 95];

import { useSession } from "@/lib/session";
import { useQuery } from "@tanstack/react-query";
import { listChatThreads } from "@/lib/api/chat-threads";
import { useEffect, useState } from "react";
import { getDashboardSummary, type DashboardSummaryResponse } from "@/lib/api/dashboard";

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
  const { session } = useSession();
  const userName = session?.user?.name ?? "Doctor";

  const [aiInsight, setAiInsight] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const analyzeWithAI = () => {
    setAnalyzing(true);
    setTimeout(() => {
      setAiInsight(
        "AI insight: Citation rate improved by 1.2% this week, indicating stronger source grounding across your workspace queries.",
      );
      setAnalyzing(false);
    }, 1200);
  };

  const { data: threadsResult, isError: isThreadsError } = useQuery({
    queryKey: ["chat-threads"],
    queryFn: () => listChatThreads(),
  });
  const threads = threadsResult || [];

  // ── Backend dashboard data ──────────────────────────────────────────
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getDashboardSummary()
      .then((data) => {
        if (!cancelled) {
          setSummary(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message ?? "Failed to load dashboard");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // ── Derived metric card values (with fallbacks) ─────────────────────
  const docStats = summary?.document_stats;
  const metricCards = {
    hoursSaved: summary?.metrics?.hours_saved ?? 0,
    indexed: docStats?.indexed ?? 0,
    processing: docStats?.processing ?? 0,
    failed: docStats?.failed ?? 0,
  };

  return (
    <AppShell>
      <PageHeader
        title={`Good morning, ${userName}`}
        description="Here's what's happening across your workspace today."
      />

      {/* ── Error banner ───────────────────────────────────────────── */}
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>Dashboard data unavailable: {error}</span>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto text-xs"
            onClick={() => window.location.reload()}
          >
            Retry
          </Button>
        </div>
      )}

      {/* ── Metric cards ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Hours saved"
          value={loading ? "—" : `${metricCards.hoursSaved}h`}
          icon={Clock}
          tone="primary"
          delta={loading ? undefined : { value: "via AI copilot", positive: true }}
          spark={sparkLatency}
        />
        <MetricCard
          label="Cited answers"
          value="94.6%"
          icon={Quote}
          tone="citation"
          delta={{ value: "+1.2%", positive: true }}
          spark={sparkCited}
        />
        <MetricCard
          label="Authorized queries"
          value="218"
          icon={Sparkles}
          tone="ai"
          delta={{ value: "+18", positive: true }}
          spark={sparkQueries}
        />
        <MetricCard
          label="Indexed documents"
          value={loading ? "—" : metricCards.indexed.toLocaleString()}
          icon={FileCheck2}
          tone="secondary"
          delta={
            loading
              ? undefined
              : metricCards.failed > 0
                ? { value: `${metricCards.failed} failed`, positive: false }
                : { value: `${metricCards.processing} processing`, positive: true }
          }
          spark={sparkDocs}
        />
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
              <Link to="/chat">
                <Sparkles className="mr-1 h-4 w-4" /> Ask
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/documents">
                <Upload className="mr-1 h-4 w-4" /> Upload
              </Link>
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
            {isThreadsError ? (
              <li className="text-sm text-destructive py-2">Failed to load threads</li>
            ) : threads.length === 0 ? (
              <li className="text-sm text-muted-foreground py-2">No recent threads</li>
            ) : (
              threads.slice(0, 4).map((t) => (
                <li key={t.id}>
                  <Link
                    to={t.patient_id ? "/chat/patients/$patientId" : "/chat"}
                    params={t.patient_id ? { patientId: t.patient_id } : undefined}
                    className="flex items-start gap-2 rounded-md p-2 hover:bg-muted"
                  >
                    <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-ai" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{t.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(t.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </Link>
                </li>
              ))
            )}
          </ul>
        </Card>
      </div>

      {/* ── Recent patients (backend-backed) ────────────────────── */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="overflow-hidden p-0 lg:col-span-2">
          <div className="flex items-center justify-between border-b p-5">
            <h3 className="text-sm font-semibold">Recent patients</h3>
            <Link
              to="/patients"
              className="inline-flex items-center text-xs font-medium text-primary hover:underline"
            >
              All patients <ArrowRight className="ml-0.5 h-3 w-3" />
            </Link>
          </div>
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : summary && summary.recent_patients.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>MRN</TableHead>
                  <TableHead>Last Accessed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summary.recent_patients.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">
                      <Link
                        to="/patients/$patientId"
                        params={{ patientId: p.id }}
                        className="hover:underline"
                      >
                        {p.full_name}
                      </Link>
                    </TableCell>
                    <TableCell className="font-mono text-xs">{p.mrn}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {p.last_accessed ? new Date(p.last_accessed).toLocaleString() : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="px-5 py-8 text-center text-sm text-muted-foreground">
              No recent patient activity.
            </div>
          )}
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Document processing</h3>
            <Link to="/documents" className="text-xs font-medium text-primary hover:underline">
              Manage
            </Link>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="mt-3 space-y-3">
              <div className="flex items-center justify-between rounded-md border p-3">
                <span className="text-sm font-medium">Indexed</span>
                <span className="text-sm font-semibold text-primary">
                  {metricCards.indexed.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-md border p-3">
                <span className="text-sm font-medium">Processing</span>
                <span className="text-sm font-semibold text-amber-500">
                  {metricCards.processing}
                </span>
              </div>
              <div className="flex items-center justify-between rounded-md border p-3">
                <span className="text-sm font-medium">Failed</span>
                <span className="text-sm font-semibold text-destructive">{metricCards.failed}</span>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* ── Charts (static data — backend doesn't serve chart series yet) */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="flex flex-col p-5">
          <h3 className="text-sm font-semibold">Lookup time — manual vs. copilot (minutes)</h3>
          <div className="mt-4 h-64 flex-1">
            <ResponsiveContainer>
              <LineChart data={lookupTimeTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="w" stroke="var(--color-muted-foreground)" fontSize={12} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line
                  type="monotone"
                  dataKey="manual"
                  stroke="var(--color-chart-5)"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="copilot"
                  stroke="var(--color-chart-1)"
                  strokeWidth={2.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 border-t pt-4">
            {aiInsight ? (
              <div className="text-sm text-muted-foreground">
                <Sparkles className="mr-1 inline-block h-4 w-4 text-ai" />
                {aiInsight}
              </div>
            ) : (
              <Button variant="outline" size="sm" onClick={analyzeWithAI} disabled={analyzing}>
                {analyzing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4 text-ai" />
                )}
                Analyze with AI
              </Button>
            )}
          </div>
        </Card>
        <Card className="flex flex-col p-5">
          <h3 className="text-sm font-semibold">Query volume — last 7 days</h3>
          <div className="mt-4 h-64 flex-1">
            <ResponsiveContainer>
              <BarChart data={dailyQueries}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="d" stroke="var(--color-muted-foreground)" fontSize={12} />
                <YAxis stroke="var(--color-muted-foreground)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="queries" fill="var(--color-chart-1)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="refused" fill="var(--color-chart-3)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 border-t pt-4">
            {aiInsight ? (
              <div className="text-sm text-muted-foreground">
                <Sparkles className="mr-1 inline-block h-4 w-4 text-ai" />
                {aiInsight}
              </div>
            ) : (
              <Button variant="outline" size="sm" onClick={analyzeWithAI} disabled={analyzing}>
                {analyzing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4 text-ai" />
                )}
                Analyze with AI
              </Button>
            )}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
