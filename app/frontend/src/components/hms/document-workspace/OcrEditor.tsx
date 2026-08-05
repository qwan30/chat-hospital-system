import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { saveDraftPage } from "@/lib/api/document-revisions";
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
  revision?: any;
  onCompare?: () => void;
}

export function OcrEditor({
  documentId,
  page,
  initialText = "",
  lockVersion: initialLockVersion,
  revision,
  onCompare,
}: OcrEditorProps) {
  const [text, setText] = useState(initialText);
  const [reason, setReason] = useState("");
  const [conflict, setConflict] = useState(false);
  const isHistorical = revision && revision.status !== "draft";
  const idempotencyKeyRef = useRef(crypto.randomUUID());

  useEffect(() => {
    setText(initialText);
    setConflict(false);
  }, [initialText]);

  const saveMutation = useMutation({
    mutationFn: (newText: string) => {
      if (initialLockVersion === undefined) {
        return Promise.reject(new Error("The latest page lock version is not loaded."));
      }
      return saveDraftPage(
        documentId,
        page,
        { corrected_text: newText, parent_revision_id: revision?.id || "", edit_reason: reason },
        { idempotencyKey: idempotencyKeyRef.current, lockVersion: initialLockVersion },
      );
    },
    onSuccess: () => {
      idempotencyKeyRef.current = crypto.randomUUID();
      setReason("");
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        setConflict(true);
      }
    },
  });

  const handleSave = () => {
    saveMutation.mutate(text);
  };

  const isSaveDisabled =
    isHistorical ||
    saveMutation.isPending ||
    reason.trim().length === 0 ||
    initialLockVersion === undefined;

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
