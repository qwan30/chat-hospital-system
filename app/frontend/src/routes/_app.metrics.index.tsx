import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { MetricCard } from "@/components/hms/MetricCard";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
const dailyQueries = [
  { d: "Mon", queries: 142, refused: 6 },
  { d: "Tue", queries: 168, refused: 9 },
  { d: "Wed", queries: 154, refused: 5 },
  { d: "Thu", queries: 191, refused: 11 },
  { d: "Fri", queries: 218, refused: 8 },
  { d: "Sat", queries: 96, refused: 3 },
  { d: "Sun", queries: 78, refused: 4 },
];
const topSources = [
  { name: "ACC/AHA Guidelines", uses: 412 },
  { name: "Hospital Formulary", uses: 318 },
  { name: "HFrEF GDMT Protocol", uses: 256 },
  { name: "Sepsis Bundle", uses: 198 },
  { name: "DOAC Renal Dosing", uses: 174 },
  { name: "Stroke Workflow", uses: 121 },
];
const latencyP95 = [
  { d: "Mon", ms: 1180 },
  { d: "Tue", ms: 1240 },
  { d: "Wed", ms: 1090 },
  { d: "Thu", ms: 1320 },
  { d: "Fri", ms: 1260 },
  { d: "Sat", ms: 980 },
  { d: "Sun", ms: 940 },
];
const citationCoverage = [
  { name: "Cited", value: 946 },
  { name: "Refused", value: 46 },
  { name: "Uncited", value: 12 },
];
const sparkQueries = [42, 51, 38, 65, 58, 72, 84];
const sparkLatency = [1.2, 1.1, 1.3, 1.0, 0.9, 1.0, 0.95];
const sparkDocs = [12200, 12380, 12510, 12640, 12720, 12800, 12842];
const sparkCited = [91, 92, 93, 92, 94, 94, 95];
import { Clock, Quote, Sparkles, FileCheck2 } from "lucide-react";

export const Route = createFileRoute("/_app/metrics/")({
  head: () => ({
    meta: [{ title: "Metrics — HMS AI Copilot" }],
  }),
  component: MetricsPage,
});

const pieColors = ["var(--color-chart-1)", "var(--color-chart-3)", "var(--color-chart-5)"];

function MetricsPage() {
  return (
    <AppShell>
      <PageHeader
        title="Metrics"
        description="Adoption, accuracy, latency, and content coverage."
        actions={
          <Button variant="outline" size="sm">
            Last 7 days
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Authorized queries"
          value="1,047"
          icon={Sparkles}
          tone="ai"
          delta={{ value: "+22%", positive: true }}
          spark={sparkQueries}
        />
        <MetricCard
          label="Cited answer rate"
          value="95.4%"
          icon={Quote}
          tone="citation"
          delta={{ value: "+0.8%", positive: true }}
          spark={sparkCited}
        />
        <MetricCard
          label="P95 latency"
          value="1.18s"
          icon={Clock}
          tone="primary"
          delta={{ value: "-90ms", positive: true }}
          spark={sparkLatency}
        />
        <MetricCard
          label="Indexed docs"
          value="12,842"
          icon={FileCheck2}
          tone="secondary"
          delta={{ value: "+412", positive: true }}
          spark={sparkDocs}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold">Query volume & refusals</h3>
          <div className="mt-4 h-72">
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
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-semibold">Answer outcomes</h3>
          <div className="mt-4 h-72">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={citationCoverage}
                  dataKey="value"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                >
                  {citationCoverage.map((_, i) => (
                    <Cell key={i} fill={pieColors[i]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="text-sm font-semibold">P95 latency (ms)</h3>
          <div className="mt-4 h-64">
            <ResponsiveContainer>
              <AreaChart data={latencyP95}>
                <defs>
                  <linearGradient id="lat" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-chart-1)" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="var(--color-chart-1)" stopOpacity={0} />
                  </linearGradient>
                </defs>
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
                <Area
                  type="monotone"
                  dataKey="ms"
                  stroke="var(--color-chart-1)"
                  strokeWidth={2}
                  fill="url(#lat)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-semibold">Top cited sources</h3>
          <div className="mt-4 h-64">
            <ResponsiveContainer>
              <BarChart data={topSources} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis type="number" stroke="var(--color-muted-foreground)" fontSize={12} />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="var(--color-muted-foreground)"
                  fontSize={11}
                  width={170}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="uses" fill="var(--color-chart-4)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
