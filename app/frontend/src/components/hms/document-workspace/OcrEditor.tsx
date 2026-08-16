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
    <div className="flex-1 flex flex-col h-full gap-3 min-h-0">
      <Textarea
        aria-label="Corrected page text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        readOnly={isHistorical}
        placeholder="Extracted OCR text will appear here..."
        className="flex-1 min-h-[300px] lg:min-h-[420px] font-mono text-xs sm:text-sm leading-relaxed p-4 rounded-xl border border-input bg-muted/20 focus-visible:ring-1 focus-visible:ring-primary shadow-inner resize-y transition-colors"
      />
      {conflict ? (
        <div className="flex items-center justify-between p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-900 dark:text-amber-200 text-xs">
          <span>This page was modified by another session. Please compare with the latest version.</span>
          <Button size="sm" variant="outline" onClick={() => onCompare?.()} className="rounded-lg">
            Compare with latest
          </Button>
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center pt-1">
          <Input
            aria-label="Edit reason"
            placeholder="Edit reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={isHistorical || saveMutation.isPending}
            className="flex-1 h-9 rounded-lg text-xs"
          />
          <Button
            onClick={handleSave}
            disabled={isSaveDisabled}
            size="sm"
            className="h-9 px-4 rounded-lg shrink-0 font-medium shadow-sm"
          >
            {saveMutation.isPending ? "Saving..." : "Save draft"}
          </Button>
        </div>
      )}
    </div>
  );
}
