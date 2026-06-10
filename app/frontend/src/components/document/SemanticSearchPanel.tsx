import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Search, FileText } from "lucide-react";
import { useState } from "react";

interface SemanticSearchPanelProps {
  onSearch: (query: string) => void;
  results?: { id: string; chunk: string; documentTitle: string; score: number }[];
}

export function SemanticSearchPanel({ onSearch, results }: SemanticSearchPanelProps) {
  const [query, setQuery] = useState("");

  return (
    <Card>
      <CardContent className="p-4 space-y-3">
        <h4 className="text-h4 text-text-strong">Semantic Search</h4>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
          <Input placeholder="Search across all documents..." value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { onSearch(query); } }} className="pl-9" />
        </div>
        {results && results.length > 0 && (
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {results.map((r) => (
              <div key={r.id} className="p-3 bg-bg-surface-tint rounded-lg border border-border-subtle hover:border-border-default transition-colors">
                <div className="flex items-center gap-2 mb-1"><FileText className="w-3 h-3 text-text-subtle" /><span className="text-[12px] font-medium text-text-default">{r.documentTitle}</span></div>
                <p className="text-[12px] text-text-muted line-clamp-2">{r.chunk}</p>
                <span className="text-[10px] text-success-600 font-medium mt-1 inline-block">{Math.round(r.score * 100)}% match</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
