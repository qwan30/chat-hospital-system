"use client";
import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { motion } from "motion/react";
import { Activity, FileText, ShieldCheck, Sparkles, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/lib/auth-context";
import { getDashboardSummary, type DashboardSummary, type RecentPatient } from "@/lib/api-client";

const chartData = [
  { day: "Mon", seconds: 142 },
  { day: "Tue", seconds: 96 },
  { day: "Wed", seconds: 68 },
  { day: "Thu", seconds: 44 },
  { day: "Fri", seconds: 29 },
];

const columns: ColumnDef<RecentPatient>[] = [
  {
    accessorKey: "full_name",
    header: "Patient",
    cell: ({ row }) => (
      <div>
        <Link href={`/patients/${row.original.id}`} style={{ textDecoration: "none" }} className="font-medium text-white hover:underline">
          {row.original.full_name}
        </Link>
        <div className="text-xs text-[#62666d]">MRN: {row.original.mrn}</div>
      </div>
    ),
  },
  {
    accessorKey: "last_accessed",
    header: "Last Accessed",
    cell: ({ row }) => {
      const val = row.original.last_accessed;
      if (!val) return <span className="text-[#62666d]">Never</span>;
      return <span className="text-[#8a8f98]">{new Date(val).toLocaleString()}</span>;
    },
  },
];

export function HospitalDashboard() {
  const router = useRouter();
  const { apiUrl, token } = useAuth();
  const [summary, setSummary] = React.useState<DashboardSummary | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    setError("");
    getDashboardSummary({ apiUrl, token })
      .then((data) => {
        setSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load dashboard statistics");
        setLoading(false);
      });
  }, [apiUrl, token]);

  const table = useReactTable({
    data: summary?.recent_patients || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (loading) {
    return (
      <main className="min-h-screen bg-[#08090a] text-white flex items-center justify-center">
        <div className="text-[#8a8f98] text-sm animate-pulse">Loading workspace summary…</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#08090a] text-white flex items-center justify-center p-6">
        <Card className="max-w-md w-full border-red-900/40 bg-red-950/10">
          <CardHeader>
            <div className="flex items-center gap-2 text-[#ffb4a8]">
              <AlertCircle className="size-5" />
              <CardTitle>Error Loading Dashboard</CardTitle>
            </div>
            <CardDescription className="text-[#ffb4a8]/70">
              The dashboard BFF summary endpoint failed to respond.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-[#ffb4a8]/60 font-mono bg-red-950/20 p-3 rounded-md border border-red-950">
              {error}
            </p>
            <Button className="w-full" onClick={() => window.location.reload()}>
              Retry Connection
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const hmsReachable = summary?.systems_health.hms_api === "healthy";
  const ollamaReachable = summary?.systems_health.ollama_inference === "healthy";

  return (
    <main className="min-h-screen bg-[#08090a] text-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-6 lg:px-8">
        <header className="flex flex-col justify-between gap-4 border-b border-white/10 pb-5 md:flex-row md:items-center">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm text-[#8a8f98]">
              <ShieldCheck className="size-4 text-[#27a644]" />
              Local-first clinical workspace
            </div>
            <h1 className="text-2xl font-medium tracking-normal md:text-3xl">Hospital Knowledge Assistant</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge className={hmsReachable ? "bg-[#27a644]/10 border-[#27a644]/40 text-[#8ef0a3]" : "bg-red-500/10 border-red-500/40 text-[#ffb4a8]"}>
              <span className={`inline-block size-1.5 rounded-full mr-1.5 ${hmsReachable ? "bg-[#8ef0a3] animate-ping" : "bg-red-400"}`} />
              {hmsReachable ? "HMS Connected" : "HMS Offline"}
            </Badge>
            <Badge className={ollamaReachable ? "bg-[#5e6ad2]/10 border-[#5e6ad2]/40 text-[#828fff]" : "bg-red-500/10 border-red-500/40 text-[#ffb4a8]"}>
              <span className={`inline-block size-1.5 rounded-full mr-1.5 ${ollamaReachable ? "bg-[#828fff] animate-ping" : "bg-red-400"}`} />
              {ollamaReachable ? "Ollama Active" : "Ollama Offline"}
            </Badge>
            <Button variant="secondary" size="sm" onClick={() => router.push("/documents")}>
              <FileText className="size-4" />
              Documents
            </Button>
            <Button size="sm" onClick={() => router.push("/chat")}>
              <Sparkles className="size-4" />
              Ask AI
            </Button>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
            <Card>
              <CardHeader>
                <CardDescription>Time Saved</CardDescription>
                <CardTitle className="text-3xl">{(summary?.metrics.hours_saved || 0).toFixed(1)} hrs</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-[#8a8f98]">
                HMS productivity hours saved via AI summary
              </CardContent>
            </Card>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
            <Card>
              <CardHeader>
                <CardDescription>Cost Optimization</CardDescription>
                <CardTitle className="text-3xl">${(summary?.metrics.cost_saved_usd || 0).toFixed(2)}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-[#8a8f98]">
                Est. savings from clinical time reduction
              </CardContent>
            </Card>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <Card>
              <CardHeader>
                <CardDescription>Knowledge Base Stats</CardDescription>
                <CardTitle className="text-3xl">{summary?.document_stats.indexed || 0} files</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-[#8a8f98]">
                {summary?.document_stats.processing || 0} processing · {summary?.document_stats.failed || 0} failed to index
              </CardContent>
            </Card>
          </motion.div>
        </section>

        <section className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Patients Accessed</CardTitle>
              <CardDescription>Audited list of patients recently reviewed by clinicians in this workspace.</CardDescription>
            </CardHeader>
            <CardContent>
              {summary?.recent_patients && summary.recent_patients.length > 0 ? (
                <Table>
                  <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                          <TableHead key={header.id}>
                            {header.isPlaceholder
                              ? null
                              : flexRender(header.column.columnDef.header, header.getContext())}
                          </TableHead>
                        ))}
                      </TableRow>
                    ))}
                  </TableHeader>
                  <TableBody>
                    {table.getRowModel().rows.map((row) => (
                      <TableRow key={row.id}>
                        {row.getVisibleCells().map((cell) => (
                          <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-[#8a8f98] text-sm">
                  No recent patient access records found.
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
