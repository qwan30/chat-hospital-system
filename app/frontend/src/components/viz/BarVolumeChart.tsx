import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface BarVolumeChartProps {
  data?: { department: string; queries: number }[];
  title?: string;
}

const CHART_COLORS = ["var(--color-chart-blue)", "var(--color-chart-green)", "var(--color-chart-orange)", "var(--color-chart-purple)", "var(--color-chart-blue)"];

export function BarVolumeChart({ data = [], title = "Queries by Department" }: BarVolumeChartProps) {
  const defaultData = [
    { department: "Cardiology", queries: 320 },
    { department: "Neurology", queries: 280 },
    { department: "Pediatrics", queries: 210 },
    { department: "Oncology", queries: 190 },
    { department: "Radiology", queries: 150 },
  ];
  const chartData = data.length > 0 ? data : defaultData;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-h4">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-chart-grid)" vertical={false} />
            <XAxis
              dataKey="department"
              tick={{ fontSize: 12, fill: "var(--color-chart-axis)" }}
              axisLine={{ stroke: "var(--color-chart-grid)" }}
              tickLine={false}
            />
            <YAxis
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
            <Bar dataKey="queries" radius={[4, 4, 0, 0]} barSize={32}>
              {chartData.map((_, index) => (
                <rect key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
