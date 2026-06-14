"use client";

import { GlobalSearch } from "@/components/layout/GlobalSearch";
import { EnvironmentPill } from "@/components/layout/EnvironmentPill";

interface TopbarProps {
  onOpenCommandPalette: () => void;
}

export function Topbar({ onOpenCommandPalette }: TopbarProps) {
  return (
    <header
      className="fixed left-[var(--sidebar-width)] top-0 right-0 z-[var(--z-topbar)] flex items-center justify-between h-[var(--topbar-height)] px-6 bg-white border-b border-border-subtle"
    >
      {/* Left section placeholder (e.g. Breadcrumbs or Page Title) */}
      <div className="flex-1"></div>

      {/* Center: Global search trigger */}
      <div className="flex-1 flex justify-center">
        <GlobalSearch onOpen={onOpenCommandPalette} />
      </div>

      {/* Right: environment pill */}
      <div className="flex-1 flex justify-end items-center gap-3">
        <EnvironmentPill />
      </div>
    </header>
  );
}
