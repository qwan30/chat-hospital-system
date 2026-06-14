"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export interface DashboardErrorStateProps {
  title?: string;
  description?: string;
  primaryAction?: { label: string; onClick: () => void };
  secondaryAction?: { label: string; onClick: () => void };
}

export function DashboardErrorState({
  title = "Unable to load dashboard",
  description = "We could not fetch dashboard metrics. Check your API connection or retry.",
  primaryAction,
  secondaryAction,
}: DashboardErrorStateProps) {
  return (
    <Card className="mx-auto mt-6 max-w-3xl border-danger-100 bg-surface p-8 text-center shadow-card">
      <AlertTriangle className="mx-auto size-10 text-danger-600" />
      <h2 className="mt-4 text-[18px] font-semibold text-strong">{title}</h2>
      <p className="mt-2 text-sm text-muted">{description}</p>
      <div className="mt-6 flex justify-center gap-3">
        {primaryAction && (
          <Button onClick={primaryAction.onClick}>{primaryAction.label}</Button>
        )}
        {secondaryAction && (
          <Button variant="outline" onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </Button>
        )}
      </div>
    </Card>
  );
}
