import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface WorkflowRow {
  name: string;
  baseline: string;
  actual: string;
  saved: string;
  pct: number;
}

const DEFAULT_WORKFLOW_ROWS: WorkflowRow[] = [
  { name: "Pre-rounding review", baseline: "22 min", actual: "8 min", saved: "14 min", pct: 64 },
  { name: "Medication reconciliation", baseline: "18 min", actual: "5 min", saved: "13 min", pct: 72 },
  { name: "Lab result interpretation", baseline: "12 min", actual: "3 min", saved: "9 min", pct: 75 },
  { name: "Documentation search", baseline: "15 min", actual: "4 min", saved: "11 min", pct: 73 },
];

interface WorkflowImpactTableProps {
  rows?: WorkflowRow[];
}

export function WorkflowImpactTable({ rows }: WorkflowImpactTableProps) {
  const items = rows || DEFAULT_WORKFLOW_ROWS;

  return (
    <Card><CardHeader><CardTitle className="text-h4">Workflow Impact</CardTitle></CardHeader>
      <CardContent>
        <table className="w-full">
          <thead><tr className="border-b border-border-subtle"><th className="text-left py-2 px-2 text-[12px] font-semibold text-text-muted">Workflow</th><th className="text-right py-2 px-2 text-[12px] font-semibold text-text-muted">Baseline</th><th className="text-right py-2 px-2 text-[12px] font-semibold text-text-muted">Actual</th><th className="text-right py-2 px-2 text-[12px] font-semibold text-text-muted">Saved</th><th className="text-right py-2 px-2 text-[12px] font-semibold text-text-muted">%</th></tr></thead>
          <tbody>{items.map((w) => <tr key={w.name} className="border-b border-border-subtle"><td className="py-2.5 px-2 text-[13px] text-text-default">{w.name}</td><td className="py-2.5 px-2 text-[13px] text-text-muted text-right">{w.baseline}</td><td className="py-2.5 px-2 text-[13px] text-text-default text-right">{w.actual}</td><td className="py-2.5 px-2 text-[13px] font-medium text-success-600 text-right">{w.saved}</td><td className="py-2.5 px-2 text-[13px] font-semibold text-primary-600 text-right">{w.pct}%</td></tr>)}</tbody>
        </table>
      </CardContent>
    </Card>
  );
}
