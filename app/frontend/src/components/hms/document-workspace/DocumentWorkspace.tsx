import { useQuery, useMutation } from "@tanstack/react-query";
import { getDocument } from "@/lib/api/documents";
import { listRevisionSets, restoreRevision } from "@/lib/api/document-revisions";
import { useState } from "react";
import { WorkspaceToolbar } from "./WorkspaceToolbar";
import { RevisionSelector } from "./RevisionSelector";
import { PageNavigator } from "./PageNavigator";
import { OcrEditor } from "./OcrEditor";
import { Button } from "@/components/ui/button";
import { RevisionHistoryDrawer } from "./RevisionHistoryDrawer";
import { DocumentPreview } from "../DocumentPreview";
import { GeometryOverlay, BoundingBox } from "./GeometryOverlay";
import { RevisionDiff } from "./RevisionDiff";

export function DocumentWorkspace({ documentId }: { documentId: string }) {
  const documentQuery = useQuery({ queryKey: ["document", documentId], queryFn: () => getDocument(documentId) });
  const revisionsQuery = useQuery({
    queryKey: ["document-revision-sets", documentId],
    queryFn: () => listRevisionSets(documentId),
  });
  
  const [selectedRevisionId, setSelectedRevisionId] = useState<string | null>(null);
  const [selectedPage, setSelectedPage] = useState(1);
  
  const restoreMutation = useMutation({
    mutationFn: () => {
      if (!selectedRevisionId) return Promise.reject(new Error("No revision"));
      return restoreRevision(
        documentId, 
        selectedRevisionId, 
        { revision_id: selectedRevisionId },
        { idempotencyKey: crypto.randomUUID() }
      );
    }
  });

  const isHistorical = selectedRevisionId && selectedRevisionId !== "draft";

  // Mocking geometry and original text for demonstration since the API doesn't provide them yet
  const geometry: BoundingBox[] = [
    { id: "1", top: 0.1, left: 0.1, width: 0.2, height: 0.05, alignment_status: "aligned" },
    { id: "2", top: 0.2, left: 0.1, width: 0.3, height: 0.05, alignment_status: "stale" }
  ];
  const exactBoxes = geometry.filter((item) => item.alignment_status === "aligned");
  const staleCount = geometry.length - exactBoxes.length;
  
  const originalText = "Patient complains of headache and nausea.\nHeart rate 80 bpm.";
  const correctedText = "Patient complains of headache and nausea.\nHeart rate 80 bpm.\n(Reviewed by MD)";

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <WorkspaceToolbar>
         <RevisionHistoryDrawer 
           revisions={revisionsQuery.data || []}
           selectedId={selectedRevisionId}
           onSelect={setSelectedRevisionId}
         />
         <div className="ml-auto flex items-center gap-2">
           <RevisionSelector 
              revisions={revisionsQuery.data || []}
              selected={selectedRevisionId}
              onSelect={setSelectedRevisionId}
           />
           <PageNavigator page={selectedPage} onPageChange={setSelectedPage} />
         </div>
      </WorkspaceToolbar>
      
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 overflow-hidden p-4 bg-muted/10">
         <div className="h-full border rounded-lg bg-background p-4 flex flex-col overflow-hidden">
           {documentQuery.data && (
             <DocumentPreview documentId={documentId} mimeType={documentQuery.data.mime_type}>
               <GeometryOverlay boxes={exactBoxes} staleCount={staleCount} />
             </DocumentPreview>
           )}
         </div>

         <div className="h-full border rounded-lg bg-background p-4 flex flex-col overflow-auto">
           {isHistorical ? (
             <div className="flex flex-col h-full">
               <h2 className="text-lg font-semibold mb-4">Revision Differences</h2>
               <RevisionDiff originalText={originalText} correctedText={correctedText} />
               <div className="mt-auto pt-4 border-t">
                 <Button onClick={() => restoreMutation.mutate()} disabled={restoreMutation.isPending}>
                   {restoreMutation.isPending ? "Restoring..." : "Restore as new revision"}
                 </Button>
               </div>
             </div>
           ) : (
             <OcrEditor 
               documentId={documentId} 
               page={selectedPage} 
               revision={{ id: selectedRevisionId, status: "draft" }} 
             />
           )}
         </div>
      </div>
    </div>
  );
}
