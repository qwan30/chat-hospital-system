"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, CircleDashed, Globe2, LockKeyhole, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { PatientContext, PatientPermissionState } from "@/lib/chat-assistant";
import { samplePatientContexts } from "@/lib/chat-assistant";

const permissionCopy: Record<
  PatientPermissionState,
  {
    icon: typeof Globe2;
    label: string;
    detail: string;
    className: string;
  }
> = {
  "not-required": {
    icon: Globe2,
    label: "General mode",
    detail: "General questions do not require patient selection. Backend citations are still a documented gap.",
    className: "border-[#60a5fa]/30 bg-[#60a5fa]/10 text-[#bfdbfe]",
  },
  pending: {
    icon: CircleDashed,
    label: "Permission pending",
    detail: "Patient-linked answers stay blocked until the backend confirms read access.",
    className: "border-[#fbbf24]/30 bg-[#fbbf24]/10 text-[#fde68a]",
  },
  allowed: {
    icon: CheckCircle2,
    label: "Permission allowed",
    detail: "Patient-linked answers may call the verified patient-scoped backend path.",
    className: "border-[#34d399]/30 bg-[#34d399]/10 text-[#bbf7d0]",
  },
  denied: {
    icon: ShieldAlert,
    label: "Permission denied",
    detail: "Patient-linked evidence and citations remain hidden for this context.",
    className: "border-[#f87171]/30 bg-[#f87171]/10 text-[#fecaca]",
  },
};

export function PatientContextGate() {
  const [activeContextId, setActiveContextId] = useState(samplePatientContexts[0]?.id ?? "");
  const activeContext = useMemo(
    () => samplePatientContexts.find((context) => context.id === activeContextId) ?? samplePatientContexts[0],
    [activeContextId],
  );

  if (!activeContext) {
    return null;
  }

  const status = permissionCopy[activeContext.permissionState];
  const StatusIcon = status.icon;

  return (
    <section className="border-b border-white/10 bg-[#0b0c0d] px-4 py-4 md:px-5" aria-labelledby="patient-gate-title">
      <div className="mx-auto grid w-full max-w-4xl gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <h2 id="patient-gate-title" className="text-sm font-semibold text-white">
              Question scope
            </h2>
            <Badge className="border-[#fbbf24]/30 text-[#fbbf24]">
              {activeContext.provenance.visibleLabel}
            </Badge>
          </div>

          <div className="grid gap-2 sm:grid-cols-2">
            {samplePatientContexts.map((context) => (
              <ContextButton
                key={context.id}
                context={context}
                selected={context.id === activeContext.id}
                onSelect={() => setActiveContextId(context.id)}
              />
            ))}
          </div>
        </div>

        <aside className={`rounded-md border p-4 ${status.className}`}>
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <StatusIcon className="size-4" />
            {status.label}
          </div>
          <p className="text-sm leading-5">{status.detail}</p>
          <div className="mt-3 flex items-start gap-2 text-xs leading-5 opacity-90">
            <LockKeyhole className="mt-0.5 size-3.5 shrink-0" />
            <span>{activeContext.provenance.note}</span>
          </div>
        </aside>
      </div>
    </section>
  );
}

function ContextButton({
  context,
  selected,
  onSelect,
}: {
  context: PatientContext;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      aria-pressed={selected}
      className={
        "min-w-0 rounded-md border px-3 py-3 text-left transition-colors " +
        (selected
          ? "border-[#5e6ad2]/60 bg-[#5e6ad2]/15 text-white"
          : "border-white/10 bg-white/[0.03] text-[#d0d6e0] hover:bg-white/[0.06]")
      }
      type="button"
      onClick={onSelect}
    >
      <span className="block truncate text-sm font-medium">{context.displayLabel}</span>
      <span className="mt-1 flex flex-wrap items-center gap-2 text-xs text-[#8a8f98]">
        <span>{context.permissionLabel}</span>
        <span aria-hidden="true">/</span>
        <span>{context.provenance.visibleLabel}</span>
      </span>
    </button>
  );
}
