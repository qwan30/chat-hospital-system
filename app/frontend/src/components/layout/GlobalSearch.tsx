"use client";

import { Search } from "lucide-react";

interface GlobalSearchProps {
  onOpen: () => void;
}

export function GlobalSearch({ onOpen }: GlobalSearchProps) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex items-center gap-3 px-4 py-2 bg-bg-surface-tint border border-border-subtle rounded-lg text-text-muted text-[13px] min-w-[320px] hover:border-border-default transition-colors"
      aria-label="Search patients, documents, threads"
    >
      <Search className="w-4 h-4 text-text-subtle flex-shrink-0" />
      <span className="flex-1 text-left">Search patients, documents, threads...</span>
      <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-bg-surface border border-border-subtle rounded text-text-subtle flex-shrink-0">
        ⌘K
      </kbd>
    </button>
  );
}
