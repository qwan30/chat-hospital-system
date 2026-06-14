"use client";

/**
 * Sidebar — Primary Navigation Component.
 *
 * Fixed-position left sidebar providing role-based navigation across the
 * hospital AI application. Renders navigation items from a centralized
 * NAV_ITEMS constant with dynamic icon resolution and active-state tracking
 * via the Next.js App Router pathname.
 *
 * @remarks
 * - Positioned as a fixed sidebar using CSS custom properties for width
 *   (`--sidebar-width`) and z-index (`--z-sidebar`).
 * - Active nav item detection uses `pathname.startsWith()` for nested route
 *   matching (e.g., `/patients/123` matches the Patients nav item).
 * - Brand lockup at top matches topbar height for visual alignment.
 * - Footer links (Settings) are separated by a top border for visual grouping.
 *
 * @example
 * ```tsx
 * // Rendered once in the app shell layout
 * <Sidebar />
 * ```
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { NAV_ITEMS, SIDEBAR_FOOTER } from "@/lib/constants";
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard, Users, MessageSquare, FileText, Clock,
  ShieldCheck, BarChart3, Settings,
} from "lucide-react";
import { BrandLockup } from "@/components/layout/BrandLockup";
import { UserMenu } from "@/components/layout/UserMenu";

/** Mapping from icon name strings to Lucide icon components for dynamic resolution. */
const ICON_MAP: Record<string, LucideIcon> = {
  LayoutDashboard, Users, MessageSquare, FileText, Clock,
  ShieldCheck, BarChart3, Settings,
};

/**
 * Renders the fixed left sidebar with dynamic navigation highlighting.
 *
 * @returns The sidebar JSX element.
 */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 z-[var(--z-sidebar)] flex flex-col bg-bg-sidebar border-r border-border-subtle overflow-hidden"
      style={{ width: "var(--sidebar-width)" }}
    >
      {/* Brand lockup — matched to topbar height */}
      <div
        className="flex items-center px-5 flex-shrink-0 border-b border-border-subtle"
        style={{ height: "var(--topbar-height)" }}
      >
        <BrandLockup variant="sidebar" showSubtitle={true} />
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
                active
                  ? "bg-primary-50 text-primary-700"
                  : "text-text-muted hover:bg-bg-surface-tint hover:text-text-default"
              )}
            >
              {Icon && <Icon className="w-[18px] h-[18px] flex-shrink-0" />}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-4 border-t border-border-subtle space-y-1 flex-shrink-0">
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors",
            pathname.startsWith("/settings")
              ? "bg-primary-50 text-primary-700"
              : "text-text-muted hover:bg-bg-surface-tint hover:text-text-default"
          )}
        >
          <Settings className="w-[18px] h-[18px] flex-shrink-0" />
          <span>Settings</span>
        </Link>

        <div className="mt-2 w-full">
          <UserMenu />
        </div>
      </div>
    </aside>
  );
}
