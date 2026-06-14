"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { globalSearch, type GlobalSearchResult } from "@/lib/api-client";
import { Search, FileText, Users, MessageSquare, ArrowRight } from "lucide-react";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const { apiUrl, token } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GlobalSearchResult | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!open) { setQuery(""); setResults(null); }
  }, [open]);

  useEffect(() => {
    if (!open || !query.trim()) { setResults(null); return; }
    const timer = setTimeout(() => {
      setSearching(true);
      globalSearch({ apiUrl, token }, query)
        .then((data) => { setResults(data); setSearching(false); })
        .catch(() => setSearching(false));
    }, 250);
    return () => clearTimeout(timer);
  }, [query, open, apiUrl, token]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") onClose();
  }, [onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[var(--z-modal)] flex justify-center" style={{ background: "var(--color-bg-overlay)", paddingTop: "12vh" }} onClick={onClose}>
      <div className="bg-bg-surface border border-border-default rounded-2xl shadow-modal w-[560px] max-h-[520px] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border-subtle">
          <Search className="w-5 h-5 text-text-subtle flex-shrink-0" />
          <input autoFocus placeholder="Search patients, documents, threads..." value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={handleKeyDown} className="flex-1 bg-transparent border-none outline-none text-[14px] text-text-default placeholder:text-text-subtle" />
          <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-bg-surface-tint border border-border-subtle rounded text-text-subtle">ESC</kbd>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {searching ? (
            <div className="text-center py-8 text-caption text-text-muted">Searching...</div>
          ) : results ? (
            <>
              {results.patients.length > 0 && (
                <CmdSection title="Patients" icon={Users} count={results.patients.length}>
                  {results.patients.slice(0, 5).map((p) => (
                    <CmdRow key={p.id} href={`/patients/${p.id}`} onClick={onClose} label={p.full_name} detail={`MRN: ${p.mrn}`} />
                  ))}
                </CmdSection>
              )}
              {results.documents.length > 0 && (
                <CmdSection title="Documents" icon={FileText} count={results.documents.length}>
                  {results.documents.slice(0, 5).map((d) => (
                    <CmdRow key={d.id} href="/documents" onClick={onClose} label={d.title} detail={d.document_type} />
                  ))}
                </CmdSection>
              )}
              {results.threads.length > 0 && (
                <CmdSection title="Chat Threads" icon={MessageSquare} count={results.threads.length}>
                  {results.threads.slice(0, 5).map((t) => (
                    <CmdRow key={t.id} href="/chat" onClick={onClose} label={t.title || "Untitled Chat Session"} />
                  ))}
                </CmdSection>
              )}
              {results.patients.length === 0 && results.documents.length === 0 && results.threads.length === 0 && (
                <div className="text-center py-8 text-caption text-text-muted">No matching records found.</div>
              )}
            </>
          ) : query.trim() ? (
            <div className="text-center py-8 text-caption text-text-muted">Type to search...</div>
          ) : (
            <div className="text-center py-8 space-y-3">
              <p className="text-caption text-text-muted">Type keywords to search across patients, documents, or threads.</p>
              <div className="flex items-center justify-center gap-2 text-[11px] text-text-subtle">
                <kbd className="px-1.5 py-0.5 bg-bg-surface-tint border border-border-subtle rounded text-[10px] font-mono">↑↓</kbd><span>Navigate</span>
                <kbd className="px-1.5 py-0.5 bg-bg-surface-tint border border-border-subtle rounded text-[10px] font-mono">↵</kbd><span>Open</span>
                <kbd className="px-1.5 py-0.5 bg-bg-surface-tint border border-border-subtle rounded text-[10px] font-mono">ESC</kbd><span>Close</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CmdSection({ title, icon: Icon, count, children }: { title: string; icon: React.ComponentType<{ className?: string }>; count: number; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 px-1 mb-2">
        <Icon className="w-3.5 h-3.5 text-text-subtle" />
        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">{title} ({count})</span>
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function CmdRow({ href, onClick, label, detail }: { href: string; onClick: () => void; label: string; detail?: string }) {
  return (
    <Link href={href} onClick={onClick} className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-bg-surface-tint transition-colors group">
      <span className="text-[13px] text-text-default font-medium">{label}</span>
      <span className="flex items-center gap-2 text-[11px] text-text-muted">
        {detail && <span>{detail}</span>}
        <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
      </span>
    </Link>
  );
}
