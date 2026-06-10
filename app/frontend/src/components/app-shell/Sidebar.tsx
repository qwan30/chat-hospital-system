"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { NAV_ITEMS, SIDEBAR_FOOTER } from "@/lib/constants";
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard, Users, MessageSquare, FileText, Clock,
  ShieldCheck, BarChart3, Settings,
} from "lucide-react";

const ICON_MAP: Record<string, LucideIcon> = {
  LayoutDashboard, Users, MessageSquare, FileText, Clock,
  ShieldCheck, BarChart3, Settings,
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 bottom-0 z-10 flex flex-col bg-bg-sidebar border-r border-border-subtle overflow-hidden" style={{ width: "244px" }}>
      <div className="flex items-center gap-2.5 px-5 flex-shrink-0 border-b border-border-subtle" style={{ height: "84px" }}>
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary-600 text-white font-bold text-base">H</div>
        <div className="flex flex-col">
          <span className="text-[12px] font-semibold text-text-strong leading-tight">Hospital AI</span>
          <span className="text-[10px] text-text-subtle leading-tight">Knowledge Assistant</span>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = ICON_MAP[item.icon];
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors",
                active ? "bg-primary-50 text-primary-700" : "text-text-muted hover:bg-bg-surface-tint hover:text-text-default"
              )}
            >
              {Icon && <Icon className="w-[18px] h-[18px] flex-shrink-0" />}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 border-t border-border-subtle space-y-1 flex-shrink-0">
        <div className="flex items-center gap-2 text-[11px] text-text-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-success-600" />
          <span>{SIDEBAR_FOOTER.auditText}</span>
        </div>
        <div className="text-[10px] text-text-subtle">{SIDEBAR_FOOTER.lastLogin}</div>
      </div>
    </aside>
  );
}
