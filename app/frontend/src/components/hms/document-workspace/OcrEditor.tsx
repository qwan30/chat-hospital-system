import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { saveDraftPage, type DraftPageRead } from "@/lib/api/document-revisions";
import { ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useRef } from "react";
interface OcrEditorProps {
  documentId: string;
  page: number;
  initialText?: string;
  lockVersion?: number;
  parentRevisionId?: string;
  revision?: any;
  onCompare?: () => void;
  onLockVersionChange?: (lockVersion: number) => void;
  onSavingChange?: (isSaving: boolean) => void;
  onSaved?: (savedPage: DraftPageRead) => void;
}

export function OcrEditor({
  documentId,
  page,
  initialText = "",
  lockVersion: initialLockVersion,
  parentRevisionId,
  revision,
  onCompare,
  onLockVersionChange,
  onSavingChange,
  onSaved,
}: OcrEditorProps) {
  const [text, setText] = useState(initialText);
  const [reason, setReason] = useState("");
  const [conflict, setConflict] = useState(false);
  const [currentLockVersion, setCurrentLockVersion] = useState(initialLockVersion);
  const isHistorical = revision && revision.status !== "draft";
  const idempotencyKeyRef = useRef(crypto.randomUUID());

  useEffect(() => {
    setText(initialText);
    setConflict(false);
  }, [initialText]);

  useEffect(() => {
    setCurrentLockVersion(initialLockVersion);
  }, [initialLockVersion]);

  const saveMutation = useMutation({
    mutationFn: (newText: string) => {
      if (currentLockVersion === undefined || !parentRevisionId) {
        return Promise.reject(new Error("The latest page revision is not loaded."));
      }
      return saveDraftPage(
        documentId,
        page,
        { text: newText, parent_revision_id: parentRevisionId, edit_reason: reason },
        { idempotencyKey: idempotencyKeyRef.current, lockVersion: currentLockVersion },
      );
    },
    onSuccess: (savedPage) => {
      setCurrentLockVersion(savedPage.lock_version);
      onLockVersionChange?.(savedPage.lock_version);
      idempotencyKeyRef.current = crypto.randomUUID();
      setReason("");
      onSaved?.(savedPage);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        setConflict(true);
      }
    },
  });

  useEffect(() => {
    onSavingChange?.(saveMutation.isPending);
  }, [onSavingChange, saveMutation.isPending]);

  const handleSave = () => {
    saveMutation.mutate(text);
  };

  const isSaveDisabled =
    isHistorical ||
    saveMutation.isPending ||
    reason.trim().length === 0 ||
    currentLockVersion === undefined ||
    !parentRevisionId;

  return (
    <div className="flex flex-col gap-4">
      <Textarea
        aria-label="Corrected page text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        readOnly={isHistorical}
      />
      {conflict ? (
        <Button variant="outline" onClick={() => onCompare?.()}>
          Compare with latest
        </Button>
      ) : (
        <div className="flex flex-col gap-2">
          <Input
            placeholder="Edit reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={isHistorical || saveMutation.isPending}
          />
          <Button onClick={handleSave} disabled={isSaveDisabled}>
            Save draft
          </Button>
        </div>
      )}
    </div>
  );
}
