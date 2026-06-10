import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CitationCard } from "./CitationCard";
import { NoEvidenceRail } from "./NoEvidenceRail";
import { RetrievalStepper } from "./RetrievalStepper";
import { FileSearch } from "lucide-react";

interface EvidenceRailProps {
  citations?: { id: number; documentTitle: string; page: number; snippet: string; confidence: number }[];
  loading?: boolean;
  onCitationClick?: (citationId: number) => void;
}

export function EvidenceRail({ citations, loading, onCitationClick }: EvidenceRailProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-h4 flex items-center gap-2"><FileSearch className="w-4 h-4 text-text-subtle" />Evidence</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? <RetrievalStepper /> : !citations || citations.length === 0 ? <NoEvidenceRail /> : (
          <div className="space-y-2">
            {citations.map((c) => <CitationCard key={c.id} id={c.id} documentTitle={c.documentTitle} page={c.page} snippet={c.snippet} confidence={c.confidence} onClick={() => onCitationClick?.(c.id)} />)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
