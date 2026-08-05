import React from "react";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export type UploadUiState = {
  kind:
    | "idle"
    | "creating_session"
    | "uploading"
    | "uploaded_unverified"
    | "verified"
    | "finalized"
    | "quarantined"
    | "rejected";
  percent?: number;
  reason?: string;
};

export function UploadStatePanel({
  state,
  onReset,
}: {
  state: UploadUiState;
  onReset: () => void;
}) {
  if (state.kind === "idle") return null;

  return (
    <div className="rounded-md border p-4 space-y-4">
      {state.kind === "creating_session" && (
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Starting upload...</span>
        </div>
      )}
      {state.kind === "uploading" && (
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Uploading... {state.percent ?? 0}%</span>
        </div>
      )}
      {state.kind === "uploaded_unverified" && (
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Verifying upload...</span>
        </div>
      )}
      {state.kind === "quarantined" && (
        <div className="flex items-center gap-2 text-destructive">
          <XCircle className="h-4 w-4" />
          <span>Upload quarantined</span>
        </div>
      )}
      {state.kind === "rejected" && (
        <div className="flex items-center gap-2 text-destructive">
          <XCircle className="h-4 w-4" />
          <span>Upload rejected</span>
        </div>
      )}
      {state.kind === "finalized" && (
        <div className="flex items-center gap-2 text-green-600">
          <CheckCircle className="h-4 w-4" />
          <span>Upload finalized</span>
        </div>
      )}
      {(state.kind === "quarantined" || state.kind === "rejected") && (
        <Button variant="outline" onClick={onReset}>
          Try again
        </Button>
      )}
    </div>
  );
}
