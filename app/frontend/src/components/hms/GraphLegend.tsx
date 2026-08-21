import React from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  Heart,
  Activity,
  Pill,
  AlertTriangle,
  FlaskConical,
  Stethoscope,
  Link2,
} from "lucide-react";

export interface RelationBadgeStyle {
  label: string;
  className: string;
  description: string;
}

export const RELATION_STYLES: Record<string, RelationBadgeStyle> = {
  treats: {
    label: "Treats",
    className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
    description: "Therapeutic treatment relationship",
  },
  causes: {
    label: "Causes",
    className: "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30",
    description: "Causal etiology or side-effect",
  },
  contraindicates: {
    label: "Contraindicates",
    className: "bg-red-500/20 text-red-700 dark:text-red-300 border-red-500/40",
    description: "Safety contraindication",
  },
  prescribed_for: {
    label: "Prescribed For",
    className: "bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-500/30",
    description: "Clinical prescription indication",
  },
  has_symptom: {
    label: "Has Symptom",
    className: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
    description: "Symptomatic manifestation",
  },
  indicates: {
    label: "Indicates",
    className: "bg-purple-500/15 text-purple-700 dark:text-purple-300 border-purple-500/30",
    description: "Diagnostic indicator or abnormal finding",
  },
  interacts_with: {
    label: "Interacts With",
    className: "bg-orange-500/15 text-orange-700 dark:text-orange-300 border-orange-500/30",
    description: "Drug-drug pharmacological interaction",
  },
  diagnosed_with: {
    label: "Diagnosed With",
    className: "bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border-indigo-500/30",
    description: "Confirmed patient diagnosis anchor",
  },
  history_of: {
    label: "History Of",
    className: "bg-slate-500/15 text-slate-700 dark:text-slate-300 border-slate-500/30",
    description: "Documented past medical history",
  },
  allergic_to: {
    label: "Allergic To",
    className: "bg-red-600/20 text-red-800 dark:text-red-200 border-red-600/40 font-medium",
    description: "Documented patient drug/substance allergy",
  },
  has_observation: {
    label: "Observation",
    className: "bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 border-cyan-500/30",
    description: "Lab test observation",
  },
  has_status: {
    label: "Status",
    className: "bg-teal-500/15 text-teal-700 dark:text-teal-300 border-teal-500/30",
    description: "Lab value status",
  },
};

export const NODE_LEGEND_ITEMS = [
  {
    type: "patient",
    label: "Patient",
    Icon: Heart,
    color: "text-primary bg-primary/10 border-primary/20",
  },
  {
    type: "encounter",
    label: "Encounter",
    Icon: Stethoscope,
    color: "text-info bg-info/10 border-info/20",
  },
  { type: "diagnosis", label: "Diagnosis", Icon: Activity, color: "text-ai bg-ai/10 border-ai/20" },
  {
    type: "medication",
    label: "Medication",
    Icon: Pill,
    color: "text-citation bg-citation/10 border-citation/20",
  },
  {
    type: "allergy",
    label: "Allergy",
    Icon: AlertTriangle,
    color: "text-destructive bg-destructive/10 border-destructive/20",
  },
  {
    type: "lab",
    label: "Lab Observation",
    Icon: FlaskConical,
    color: "text-warning bg-warning/10 border-warning/20",
  },
];

export interface GraphLegendProps {
  hiddenTypes?: Set<string>;
  onToggleType?: (type: string) => void;
  selectedRelationTypes?: string[];
  onToggleRelationType?: (relation: string) => void;
}

export function GraphLegend({
  hiddenTypes,
  onToggleType,
  selectedRelationTypes,
  onToggleRelationType,
}: GraphLegendProps = {}) {
  return (
    <Card className="p-4 space-y-4 text-xs">
      <div>
        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-primary" />
          Entity Nodes
        </h4>
        <div className="grid grid-cols-2 gap-2">
          {NODE_LEGEND_ITEMS.map(({ type, label, Icon, color }) => {
            const isOff = hiddenTypes?.has(type);
            return (
              <button
                key={type}
                type="button"
                onClick={() => onToggleType?.(type)}
                className={cn(
                  "flex items-center gap-2 px-2 py-1 rounded border transition-all text-left",
                  onToggleType ? "cursor-pointer hover:shadow-xs" : "cursor-default",
                  color,
                  isOff && "opacity-40 border-dashed grayscale bg-muted/40 text-muted-foreground",
                )}
                title={isOff ? `Show ${label} nodes` : `Hide ${label} nodes`}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span className={cn(isOff && "line-through opacity-80")}>{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="pt-2 border-t">
        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-1.5">
          <Link2 className="h-3.5 w-3.5 text-primary" />
          Clinical Relations (10 Standard Types)
        </h4>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(RELATION_STYLES).map(([key, style]) => {
            const isSelected = selectedRelationTypes?.includes(key);
            return (
              <button
                key={key}
                type="button"
                onClick={() => onToggleRelationType?.(key)}
                className={cn(onToggleRelationType ? "cursor-pointer" : "cursor-default")}
              >
                <Badge
                  variant="outline"
                  className={cn(
                    style.className,
                    "text-[11px] py-0.5 transition-all",
                    isSelected && "ring-2 ring-primary ring-offset-1 font-semibold scale-105",
                  )}
                  title={style.description}
                >
                  {style.label}
                </Badge>
              </button>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
