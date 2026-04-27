"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { motion } from "motion/react";
import { Activity, FileText, Search, ShieldCheck, Sparkles } from "lucide-react";
import { useForm } from "react-hook-form";
import { Area, AreaChart, Tooltip, XAxis, YAxis } from "recharts";
import { z } from "zod";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type PatientRow = {
  id: string;
  patient: string;
  scope: string;
  status: "Indexed" | "OCR Pending" | "Review";
  updated: string;
};

const querySchema = z.object({
  query: z.string().min(8, "Enter at least 8 characters."),
});

type QueryValues = z.infer<typeof querySchema>;

const patientRows: PatientRow[] = [
  { id: "P-1042", patient: "Nguyen Minh A", scope: "Cardiology", status: "Indexed", updated: "2 min ago" },
  { id: "P-1188", patient: "Tran Bao C", scope: "Pharmacy", status: "Review", updated: "18 min ago" },
  { id: "P-1307", patient: "Le An K", scope: "Records", status: "OCR Pending", updated: "41 min ago" },
];

const chartData = [
  { day: "Mon", seconds: 142 },
  { day: "Tue", seconds: 96 },
  { day: "Wed", seconds: 68 },
  { day: "Thu", seconds: 44 },
  { day: "Fri", seconds: 29 },
];

const columns: ColumnDef<PatientRow>[] = [
  {
    accessorKey: "patient",
    header: "Patient",
    cell: ({ row }) => (
      <div>
        <div className="font-medium text-white">{row.original.patient}</div>
        <div className="text-xs text-[#62666d]">{row.original.id}</div>
      </div>
    ),
  },
  {
    accessorKey: "scope",
    header: "Scope",
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => (
      <Badge className={row.original.status === "Indexed" ? "border-[#27a644]/40 text-[#8ef0a3]" : undefined}>
        {row.original.status}
      </Badge>
    ),
  },
  {
    accessorKey: "updated",
    header: "Updated",
  },
];

export function HospitalDashboard() {
  const [submittedQuery, setSubmittedQuery] = React.useState("Summarize recent cardiology notes with citations");
  const chartRef = React.useRef<HTMLDivElement>(null);
  const [chartSize, setChartSize] = React.useState({ width: 0, height: 0 });
  const form = useForm<QueryValues>({
    resolver: zodResolver(querySchema),
    defaultValues: {
      query: submittedQuery,
    },
  });

  React.useEffect(() => {
    const chartElement = chartRef.current;

    if (!chartElement) {
      return undefined;
    }

    const observer = new ResizeObserver(([entry]) => {
      const width = Math.floor(entry.contentRect.width);
      const height = Math.floor(entry.contentRect.height);

      if (width > 0 && height > 0) {
        setChartSize({ width, height });
      }
    });

    observer.observe(chartElement);

    return () => observer.disconnect();
  }, []);

  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data: patientRows,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  function onSubmit(values: QueryValues) {
    setSubmittedQuery(values.query);
  }

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
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm">
              <FileText className="size-4" />
              Documents
            </Button>
            <Button size="sm">
              <Sparkles className="size-4" />
              Ask AI
            </Button>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          {[
            ["Lookup Time", "29 sec", "MVP target under 30 sec"],
            ["Citation Rate", "96%", "Evidence-backed answers"],
            ["Unauthorized Chunks", "0", "Permission filter before RAG"],
          ].map(([title, value, detail]) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.28 }}
            >
              <Card>
                <CardHeader>
                  <CardDescription>{title}</CardDescription>
                  <CardTitle className="text-3xl">{value}</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-[#8a8f98]">{detail}</CardContent>
              </Card>
            </motion.div>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <Card>
            <CardHeader>
              <CardTitle>Patient Worklist</CardTitle>
              <CardDescription>Vercel-inspired dashboard density for high-signal clinical operations.</CardDescription>
            </CardHeader>
            <CardContent>
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Lookup Performance</CardTitle>
              <CardDescription>Recharts area view for workflow speed metrics.</CardDescription>
            </CardHeader>
            <CardContent className="h-64">
              <div ref={chartRef} className="h-full min-h-[220px] w-full">
                {chartSize.width > 0 && chartSize.height > 0 ? (
                  <AreaChart
                    width={chartSize.width}
                    height={chartSize.height}
                    data={chartData}
                    margin={{ left: -20, right: 8, top: 8, bottom: 0 }}
                  >
                    <XAxis dataKey="day" stroke="#62666d" tickLine={false} axisLine={false} />
                    <YAxis stroke="#62666d" tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "#191a1b",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: 8,
                        color: "#f7f8f8",
                      }}
                    />
                    <Area type="monotone" dataKey="seconds" stroke="#7170ff" fill="#5e6ad2" fillOpacity={0.25} />
                  </AreaChart>
                ) : (
                  <div className="h-full rounded-md bg-white/[0.03]" />
                )}
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Clinical Query</CardTitle>
              <CardDescription>React Hook Form plus Zod validation.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="grid gap-3" onSubmit={form.handleSubmit(onSubmit)}>
                <Label htmlFor="query">Question</Label>
                <div className="flex gap-2">
                  <Input id="query" {...form.register("query")} />
                  <Button type="submit" size="icon" aria-label="Submit clinical query">
                    <Search className="size-4" />
                  </Button>
                </div>
                {form.formState.errors.query ? (
                  <p className="text-sm text-[#ffb4a8]">{form.formState.errors.query.message}</p>
                ) : null}
              </form>
            </CardContent>
          </Card>

          <Card className="bg-[#f7f8f8] text-[#171717]">
            <CardHeader>
              <div className="mb-2 flex items-center gap-2 text-sm text-[#615d59]">
                <Activity className="size-4" />
                Notion-lite document surface
              </div>
              <CardTitle className="text-[#171717]">Cited Answer Draft</CardTitle>
              <CardDescription className="text-[#615d59]">{submittedQuery}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-[#31302e]">
              <p>
                Recent notes indicate stable vitals, a cardiology follow-up, and medication adherence review.
              </p>
              <p className="rounded-md border border-black/10 bg-white p-3 text-xs text-[#615d59]">
                Citation: Cardiology note, Lab summary, Medication reconciliation.
              </p>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
