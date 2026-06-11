import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface QualitySafetyChartProps {
  data?: { date: string; accuracy: number; safety: number }[];
  title?: string;
}

export function QualitySafetyChart({ data = [], title = "Quality & Safety Metrics" }: QualitySafetyChartProps) {
  const defaultData = [
    { date: "Week 1", accuracy: 92, safety: 88 },
    { date: "Week 2", accuracy: 94, safety: 90 },
    { date: "Week 3", accuracy: 93, safety: 92 },
    { date: "Week 4", accuracy: 96, safety: 91 },
    { date: "Week 5", accuracy: 95, safety: 94 },
    { date: "Week 6", accuracy: 97, safety: 95 },
  ];
  const chartData = data.length > 0 ? data : defaultData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-h4">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4 mb-2">
          <span className="flex items-center gap-1.5 text-[12px] text-text-muted">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "var(--color-chart-green)" }} />
            Accuracy
          </span>
          <span className="flex items-center gap-1.5 text-[12px] text-text-muted">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "var(--color-chart-blue)" }} />
            Safety
          </span>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-chart-grid)" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: "var(--color-chart-axis)" }}
              axisLine={{ stroke: "var(--color-chart-grid)" }}
              tickLine={false}
            />
            <YAxis
              domain={[80, 100]}
              tick={{ fontSize: 12, fill: "var(--color-chart-axis)" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-bg-surface)",
                border: "1px solid var(--color-border-default)",
                borderRadius: 8,
                fontSize: 13,
              }}
            />
            <Area
              type="monotone"
              dataKey="accuracy"
              stroke="var(--color-chart-green)"
              fill="var(--color-chart-green)"
              fillOpacity={0.1}
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="safety"
              stroke="var(--color-chart-blue)"
              fill="var(--color-chart-blue)"
              fillOpacity={0.1}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
