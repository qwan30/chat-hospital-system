"use client";

import { ArrowUpDown } from "lucide-react";
import Link from "next/link";

export interface PatientListRowProps {
  id: string;
  fullName: string;
  mrn: string;
  department?: string;
  status?: string;
}

function getInitials(fullName: string): string {
  return fullName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

function getStatusBadgeClasses(status: string): string {
  switch (status) {
    case "active":
      return "bg-success-50 text-success-600";
    case "admitted":
      return "bg-primary-50 text-primary-600";
    default:
      return "bg-bg-surface-tint text-text-muted";
  }
}

export function PatientListRow({
  id,
  fullName,
  mrn,
  department,
  status,
}: PatientListRowProps) {
  const initials = getInitials(fullName);

  return (
    <Link
      href={"/patients/" + id}
      className="flex items-center justify-between p-4 bg-bg-surface rounded-xl border border-border-subtle hover:border-border-default hover:shadow-card transition-all group"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-[13px] font-semibold">
          {initials}
        </div>
        <div>
          <p className="text-[14px] font-semibold text-text-default group-hover:text-primary-600 transition-colors">
            {fullName}
          </p>
          <p className="text-[12px] text-text-muted">
            MRN: {mrn}
            {department ? " · " + department : ""}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {status && (
          <span
            className={
              "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium " +
              getStatusBadgeClasses(status)
            }
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        )}
        <ArrowUpDown className="w-4 h-4 text-text-subtle" />
      </div>
    </Link>
  );
}
