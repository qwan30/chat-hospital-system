import { useState, useEffect, useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import { saveDraftPage, type DraftPageRead } from "@/lib/api/document-revisions";
import { ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useRef } from "react";
import { Save, MessageSquare, Check, AlertCircle } from "lucide-react";

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

  const hasUnsavedChanges = text !== initialText;

  const stats = useMemo(() => {
    const trimmed = text.trim();
    const words = trimmed ? trimmed.split(/\s+/).length : 0;
    const chars = text.length;
    const lines = text.split("\n").length;
    return { words, chars, lines };
  }, [text]);

  const saveMutation = useMutation({
    mutationFn: (newText: string) => {
      const lockVer = currentLockVersion ?? 1;
      const parentId = parentRevisionId;
      if (!parentId) {
        return Promise.reject(new Error("The latest page revision is not loaded."));
      }
      return saveDraftPage(
        documentId,
        page,
        {
          text: newText,
          parent_revision_id: parentId,
          edit_reason: reason.trim() || "Manual OCR text update",
        },
        { idempotencyKey: idempotencyKeyRef.current, lockVersion: lockVer },
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
    if (isSaveDisabled) return;
    saveMutation.mutate(text);
  };

  const isSaveDisabled =
    isHistorical ||
    saveMutation.isPending ||
    (!hasUnsavedChanges && !reason.trim());

  // Handle Ctrl+S / Cmd+S
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      if (!isSaveDisabled) {
        handleSave();
      }
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full gap-3 min-h-0">
      <div className="relative flex-1 flex flex-col min-h-0">
        <Textarea
          aria-label="Corrected page text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          readOnly={isHistorical}
          placeholder="Extracted OCR text will appear here..."
          className="flex-1 w-full min-h-0 font-mono text-xs sm:text-sm leading-relaxed p-4 rounded-xl border border-input/80 bg-background/80 focus-visible:ring-1 focus-visible:ring-primary shadow-inner resize-none transition-colors"
        />

        <div className="flex items-center justify-between px-3 py-1.5 text-[11px] text-muted-foreground bg-muted/30 border-x border-b rounded-b-xl select-none">
          <div className="flex items-center gap-3">
            <span>{stats.lines} lines</span>
            <span>{stats.words} words</span>
            <span>{stats.chars} chars</span>
          </div>
          <div className="flex items-center gap-1.5">
            {hasUnsavedChanges ? (
              <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400 font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
                Unsaved edits
              </span>
            ) : (
              <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                <Check className="h-3 w-3" />
                Saved to draft
              </span>
            )}
          </div>
        </div>
      </div>

      {conflict ? (
        <div className="flex items-center justify-between p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-200 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
            <span>This page was modified by another session. Please compare with the latest version.</span>
          </div>
          <Button size="sm" variant="outline" onClick={() => onCompare?.()} className="rounded-lg h-7 text-xs">
            Compare with latest
          </Button>
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center bg-card/60 p-2.5 rounded-xl border border-border/80 shadow-sm">
          <div className="relative flex-1">
            <MessageSquare className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              aria-label="Edit reason"
              placeholder="Edit reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={isHistorical || saveMutation.isPending}
              className="pl-8 h-8 rounded-lg text-xs bg-background/80"
            />
          </div>
          <Button
            onClick={handleSave}
            disabled={isSaveDisabled}
            size="sm"
            className="h-8 px-3.5 rounded-lg shrink-0 font-medium text-xs shadow-sm gap-1.5"
          >
            <Save className="h-3.5 w-3.5" />
            {saveMutation.isPending ? "Saving..." : "Save draft"}
          </Button>
        </div>
      )}
    </div>
  );
}
