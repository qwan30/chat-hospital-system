"use client";

import { ChevronDown, Database, FlaskConical, GraduationCap, Lock } from "lucide-react";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { CURRENT_ENVIRONMENT } from "@/lib/constants";

const ENVIRONMENTS = [
  {
    id: "synthetic",
    label: "Synthetic Data",
    desc: "Mock patient datasets. Safe for testing.",
    icon: Database,
    color: "text-primary-600 bg-primary-50",
    active: true,
  },
  {
    id: "sandbox",
    label: "Sandbox",
    desc: "Isolated environment for development.",
    icon: FlaskConical,
    color: "text-warning-500 bg-warning-100",
  },
  {
    id: "training",
    label: "Training Mode",
    desc: "De-identified historical charts.",
    icon: GraduationCap,
    color: "text-purple-600 bg-purple-100",
  },
  {
    id: "production",
    label: "Production Data",
    desc: "Live hospital intranet data. Strict ABAC.",
    icon: Lock,
    color: "text-danger-600 bg-danger-100",
  },
];

export function EnvironmentPill() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 px-3 py-1.5 text-[12px] font-medium text-text-muted bg-bg-surface-tint border border-border-subtle rounded-lg hover:border-border-default transition-colors">
          <span className="w-2 h-2 rounded-full bg-primary-500" />
          {CURRENT_ENVIRONMENT}
          <ChevronDown className="w-3 h-3 ml-1" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[310px]">
        <DropdownMenuLabel className="text-caption-strong text-text-muted">
          Environment
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {ENVIRONMENTS.map((env) => {
          const Icon = env.icon;
          return (
            <DropdownMenuItem
              key={env.id}
              className="flex items-start gap-3 py-3 cursor-pointer"
              onClick={() => {
                if (!env.active)
                  toast("Environment changed", {
                    description: `Switched to ${env.label}`,
                  });
              }}
            >
              <span
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${env.color}`}
              >
                <Icon className="w-4 h-4" />
              </span>
              <div className="flex flex-col gap-0.5">
                <span className="text-body-strong text-text-default">
                  {env.label}
                </span>
                <span className="text-caption text-text-muted">{env.desc}</span>
              </div>
              {env.active && (
                <span className="ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded bg-success-50 text-success-600">
                  Current
                </span>
              )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
