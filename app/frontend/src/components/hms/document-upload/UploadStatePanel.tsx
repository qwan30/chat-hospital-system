import React from "react";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export type UploadUiState = {
  kind:
    | "idle"
    | "creating_session"
    | "uploading"
    | "pending"
    | "uploaded_unverified"
    | "verified"
    | "finalized"
    | "quarantined"
    | "rejected";
  percent?: number;
  reason?: string;
  checksum?: string;
  mime?: string;
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
      {state.kind === "pending" && (
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Pending verification...</span>
        </div>
      )}
      {state.kind === "verified" && (
        <div className="flex items-center gap-2 text-emerald-600">
          <CheckCircle className="h-4 w-4" />
          <span>Upload verified</span>
          {state.reason && <span className="text-sm">({state.reason})</span>}
        </div>
      )}
      {state.kind === "quarantined" && (
        <div className="flex flex-col gap-2 text-destructive">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4" />
            <span>Upload quarantined</span>
          </div>
          {state.reason && <p className="text-sm">Reason: {state.reason}</p>}
          {state.checksum && <p className="text-sm">Checksum: {state.checksum}</p>}
          {state.mime && <p className="text-sm">MIME: {state.mime}</p>}
        </div>
      )}
      {state.kind === "rejected" && (
        <div className="flex flex-col gap-2 text-destructive">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4" />
            <span>Upload rejected</span>
          </div>
          {state.reason && <p className="text-sm">Reason: {state.reason}</p>}
          {state.checksum && <p className="text-sm">Checksum: {state.checksum}</p>}
          {state.mime && <p className="text-sm">MIME: {state.mime}</p>}
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
