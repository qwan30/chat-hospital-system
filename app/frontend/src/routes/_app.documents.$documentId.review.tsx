import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { OcrConfidenceBadge } from "@/components/hms/OcrConfidenceBadge";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getDocument,
  getDocumentFacts,
  getDocumentReviewItems,
  patchReviewItem,
} from "@/lib/api/documents";
import { Loader2, Check, X, Edit2 } from "lucide-react";
import { DocumentPreview } from "@/components/hms/DocumentPreview";
import { GeometryOverlay } from "@/components/hms/document-workspace/GeometryOverlay";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";

export const Route = createFileRoute("/_app/documents/$documentId/review")({
  head: () => ({ meta: [{ title: "OCR review — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { documentId } = Route.useParams();
  const queryClient = useQueryClient();

  const [activeFactId, setActiveFactId] = useState<string | null>(null);

  const { data: document, isLoading: isDocLoading } = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
  });

  const { data: factsData, isLoading: isFactsLoading } = useQuery({
    queryKey: ["document-facts", documentId],
    queryFn: () => getDocumentFacts(documentId),
  });

  const { data: reviewsData, isLoading: isReviewsLoading } = useQuery({
    queryKey: ["document-reviews", documentId],
    queryFn: () => getDocumentReviewItems(documentId),
  });

  const patchMutation = useMutation({
    mutationFn: ({
      reviewItemId,
      action,
      value,
      reason,
    }: {
      reviewItemId: string;
      action: "approve" | "reject" | "correct";
      value?: any;
      reason: string;
    }) =>
      patchReviewItem(documentId, reviewItemId, {
        action,
        value,
        reason,
      }),
    onSuccess: () => {
      toast.success("Review item updated");
      queryClient.invalidateQueries({ queryKey: ["document-reviews", documentId] });
      queryClient.invalidateQueries({ queryKey: ["document-facts", documentId] });
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Failed to update review item");
    },
  });

  const isLoading = isDocLoading || isFactsLoading || isReviewsLoading;
  const activeFact = factsData?.facts.find((f) => f.id === activeFactId);

  return (
    <AppShell>
      <PageHeader
        title="OCR review"
        description="Low-confidence regions flagged for human verification."
        backLink={{ to: `/documents/${documentId}`, label: "Back to Document" }}
      />
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-5 flex flex-col h-[600px]">
          {isDocLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : document ? (
            <DocumentPreview
              documentId={document.id}
              mimeType={document.mime_type}
            >
              {activeFact?.bounding_box && (
                <GeometryOverlay
                  boxes={[{ id: activeFact.id, ...activeFact.bounding_box, alignment_status: "aligned" }]}
                  staleCount={0}
                />
              )}
            </DocumentPreview>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              Document not found
            </div>
          )}
        </Card>
        <Card className="p-5 space-y-3 text-sm flex flex-col h-[600px] overflow-y-auto">
          {isLoading ? (
            <div className="flex flex-1 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : reviewsData?.review_items.length === 0 ? (
            <div className="flex flex-1 items-center justify-center text-muted-foreground">
              No items require review.
            </div>
          ) : (
            reviewsData?.review_items.map((item) => (
              <ReviewItemCard
                key={item.id}
                item={item}
                fact={factsData?.facts.find((f) => f.id === item.fact_id)}
                patchMutation={patchMutation}
                isActive={activeFactId === item.fact_id}
                onActivate={() => setActiveFactId(item.fact_id || null)}
              />
            ))
          )}
        </Card>
      </div>
    </AppShell>
  );
}

function ReviewItemCard({
  item,
  fact,
  patchMutation,
  isActive,
  onActivate,
}: {
  item: any;
  fact: any;
  patchMutation: any;
  isActive: boolean;
  onActivate: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(item.suggested_value || item.original_value || "");
  const [reason, setReason] = useState("");

  const handleAction = (action: "approve" | "reject" | "correct") => {
    let finalReason = reason;
    if (!finalReason) {
      if (action === "approve") finalReason = "Verified by user";
      if (action === "reject") finalReason = "Rejected by user";
      if (action === "correct") finalReason = "Corrected by user";
    }

    let payloadValue = {};
    if (action === "approve") {
      payloadValue = { [item.field_name]: item.suggested_value || item.original_value };
    } else if (action === "correct") {
      payloadValue = editValue; // sending raw editValue
    }

    patchMutation.mutate({
      reviewItemId: item.id,
      action,
      value: payloadValue,
      reason: finalReason,
    });
    setIsEditing(false);
  };

  return (
    <div
      className={`flex flex-col gap-2 rounded-md border p-3 cursor-pointer transition-colors ${isActive ? "bg-muted/50 border-primary/50" : "bg-card hover:bg-muted/20"}`}
      onClick={onActivate}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs text-muted-foreground capitalize">
            {item.field_name.replace(/_/g, " ")}
          </p>
          {isEditing ? (
            <Input
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="h-8 mt-1 text-sm"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <p className="font-medium text-base mt-0.5">
              {item.suggested_value || item.original_value}
            </p>
          )}
        </div>
        {fact?.confidence != null && !isEditing && (
          <OcrConfidenceBadge confidence={fact.confidence} />
        )}
      </div>

      <div
        className="flex flex-col gap-2 mt-2 pt-2 border-t border-border/50"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 w-full">
          <Badge
            variant={
              item.review_status === "pending"
                ? "secondary"
                : item.review_status === "approved"
                  ? "default"
                  : "destructive"
            }
            className="capitalize text-[10px]"
          >
            {item.review_status}
          </Badge>

          {item.review_status === "pending" && (
            <div className="ml-auto flex gap-2 items-center">
              <Input
                placeholder="Reason (optional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="h-7 text-xs w-32"
              />

              {!isEditing ? (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 px-2"
                    onClick={() => setIsEditing(true)}
                  >
                    <Edit2 className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                    onClick={() => handleAction("reject")}
                    disabled={patchMutation.isPending}
                  >
                    <X className="h-3 w-3 mr-1" />
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 px-2 text-green-600 hover:text-green-700 hover:bg-green-50 border-green-200"
                    onClick={() => handleAction("approve")}
                    disabled={patchMutation.isPending}
                  >
                    <Check className="h-3 w-3 mr-1" />
                    Approve
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 px-2"
                    onClick={() => setIsEditing(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    className="h-7 px-2"
                    onClick={() => handleAction("correct")}
                    disabled={patchMutation.isPending || !editValue}
                  >
                    Save & Approve
                  </Button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
