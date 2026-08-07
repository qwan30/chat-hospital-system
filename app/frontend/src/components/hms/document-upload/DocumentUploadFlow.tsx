import React, { useRef, useState, useEffect } from "react";
import { UploadUiState, UploadStatePanel } from "./UploadStatePanel";
import {
  createUploadSession,
  putPresignedObject,
  finalizeUpload,
  UploadFinalizeResult,
  getDocument,
} from "@/lib/api/documents";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useNavigate } from "@tanstack/react-router";

export function DocumentUploadFlow({
  patientId,
  documentType = "clinical_note",
  title = "",
}: {
  patientId: string;
  documentType?: string;
  title?: string;
}) {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadUiState>({ kind: "idle" });
  const key = useRef<string>(crypto.randomUUID());
  const isMounted = useRef<boolean>(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
    key.current = crypto.randomUUID();
    setState({ kind: "idle" });
  };

  const uploadResultToUiState = (result: UploadFinalizeResult): UploadUiState => {
    switch (result.state) {
      case "pending":
        return { kind: "pending", reason: result.reason };
      case "finalized":
        return { kind: "finalized", reason: result.reason };
      case "quarantined":
        return { kind: "quarantined", reason: result.reason };
      case "rejected":
        return { kind: "rejected", reason: result.reason };
      case "verified":
        return { kind: "verified", reason: result.reason };
      default:
        return { kind: "uploaded_unverified", reason: result.reason };
    }
  };

  const hashFile = async (file: File): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  };

  const runUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      setState({ kind: "creating_session" });
      const sha256 = await hashFile(file);
      const session = await createUploadSession(
        {
          patient_id: patientId,
          title: title,
          document_type: documentType,
          filename: file.name,
          expected_size: file.size,
          expected_sha256: sha256,
          claimed_mime_type: file.type || "application/octet-stream",
        },
        { idempotencyKey: key.current },
      );

      setState({ kind: "uploading", percent: 0 });
      await putPresignedObject(session, file, (percent) =>
        setState({ kind: "uploading", percent }),
      );

      setState({ kind: "uploaded_unverified" });
      const result = await finalizeUpload(session.document_id, session.upload_id, {
        idempotencyKey: key.current,
      });

      let nextState = uploadResultToUiState(result);
      if (nextState.kind === "quarantined" || nextState.kind === "rejected") {
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
        nextState = {
          ...nextState,
          checksum: sha256,
          mime: file.type || "application/octet-stream",
        };
      }
      setState(nextState);

      if (nextState.kind === "finalized") {
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
        navigate({ to: "/documents/$documentId", params: { documentId: result.document_id } });
      } else if (nextState.kind === "verified" || nextState.kind === "pending") {
        let isFinal = false;
        while (!isFinal) {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          if (!isMounted.current) return;
          const projection = await getDocument(result.document_id);
          if (projection.status === "review_required" || projection.status === "ready") {
            isFinal = true;
            setFile(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
            navigate({ to: "/documents/$documentId", params: { documentId: result.document_id } });
          } else if (
            projection.status === "quarantined" ||
            projection.status === "rejected" ||
            projection.status === "failed"
          ) {
            isFinal = true;
            setFile(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
            setState({
              kind: projection.status === "quarantined" ? "quarantined" : "rejected",
              reason: projection.ocr_error || "Processing failed",
              checksum: sha256,
              mime: file.type || "application/octet-stream",
            });
          }
        }
      }
    } catch (err) {
      setState({
        kind: "rejected",
        reason: err instanceof Error ? err.message : String(err),
      });
    }
  };

  return (
    <div className="space-y-6">
      <form id="upload-form" onSubmit={runUpload} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="file-upload">Clinical document</Label>
          <Input
            id="file-upload"
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            disabled={
              state.kind !== "idle" && state.kind !== "quarantined" && state.kind !== "rejected"
            }
          />
        </div>
        <Button
          type="submit"
          disabled={
            !file ||
            (state.kind !== "idle" && state.kind !== "quarantined" && state.kind !== "rejected")
          }
        >
          Upload document
        </Button>
      </form>
      <UploadStatePanel
        state={state}
        onReset={() => {
          setState({ kind: "idle" });
          setFile(null);
          if (fileInputRef.current) fileInputRef.current.value = "";
        }}
      />
    </div>
  );
}
