import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { saveDraftPage } from "@/lib/api/document-revisions";
import { ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface OcrEditorProps {
  documentId: string;
  page: number;
  initialText?: string;
  lockVersion?: number;
  revision?: any;
}

export function OcrEditor({ documentId, page, initialText = "", lockVersion: initialLockVersion, revision }: OcrEditorProps) {
  const [text, setText] = useState(initialText);
  const [conflict, setConflict] = useState(false);
  const isHistorical = revision && revision.status !== "draft";

  useEffect(() => {
    setText(initialText);
    setConflict(false);
  }, [initialText]);

  const saveMutation = useMutation({
    mutationFn: (newText: string) => {
      return saveDraftPage(
        documentId, 
        page, 
        { text: newText, parent_revision_id: revision?.id || "" }, 
        { idempotencyKey: crypto.randomUUID(), lockVersion: initialLockVersion }
      );
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        setConflict(true);
      }
    }
  });

  const handleSave = () => {
    saveMutation.mutate(text);
  };

  return (
    <div className="flex flex-col gap-4">
      <Textarea
        aria-label="Corrected page text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        readOnly={isHistorical}
      />
      {conflict ? (
        <Button variant="outline">Compare with latest</Button>
      ) : (
        <Button onClick={handleSave} disabled={isHistorical || saveMutation.isPending}>
          Save draft
        </Button>
      )}
    </div>
  );
}
