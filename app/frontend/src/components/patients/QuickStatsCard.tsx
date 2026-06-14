"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export interface QuickStatsCardProps {
  total: number;
  showing: number;
}

export function QuickStatsCard({ total, showing }: QuickStatsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-h4">Quick Stats</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-text-muted">Total Patients</span>
          <span className="text-[14px] font-semibold text-text-default">
            {total}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-text-muted">Showing</span>
          <span className="text-[14px] font-semibold text-text-default">
            {showing}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
