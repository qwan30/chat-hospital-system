"use client";

import { CircleSlash } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface EmptyStateCardProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyStateCard({
  icon,
  title,
  description,
  action,
}: EmptyStateCardProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6">
      <div className="w-20 h-20 rounded-2xl bg-primary-50 flex items-center justify-center mb-6">
        {icon ?? <CircleSlash className="w-10 h-10 text-primary-400" />}
      </div>
      <h2 className="text-h2 text-text-strong mb-3">{title}</h2>
      {description && (
        <p className="text-body text-text-muted max-w-lg text-center mb-8">
          {description}
        </p>
      )}
      {action && (
        <Button onClick={action.onClick}>{action.label}</Button>
      )}
    </div>
  );
}
