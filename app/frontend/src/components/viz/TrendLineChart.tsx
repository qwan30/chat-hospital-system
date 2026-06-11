import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface TrendLineChartProps {
  data?: { date: string; value: number }[];
  title?: string;
  trend?: { direction: "up" | "down"; percentage: number };
}

export function TrendLineChart({ data = [], title = "Query Volume Trend", trend }: TrendLineChartProps) {
  const defaultData = [
    { date: "Mon", value: 120 },
    { date: "Tue", value: 200 },
    { date: "Wed", value: 150 },
    { date: "Thu", value: 280 },
    { date: "Fri", value: 220 },
    { date: "Sat", value: 180 },
    { date: "Sun", value: 240 },
  ];
  const chartData = data.length > 0 ? data : defaultData;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-h4">{title}</CardTitle>
        {trend && (
          <span
            className="text-[13px] font-semibold flex items-center gap-1"
            style={{ color: trend.direction === "up" ? "var(--color-chart-green)" : "var(--color-danger-600)" }}
          >
            {trend.direction === "up" ? "+" : "-"}{trend.percentage}%
          </span>
        )}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-chart-grid)" vertical={false} />
            <XAxis
              dataKey="date"
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
            <Line
              type="monotone"
              dataKey="value"
              stroke="var(--color-chart-blue)"
              strokeWidth={2}
              dot={{ fill: "var(--color-chart-blue)", r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
