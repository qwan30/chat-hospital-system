import { useState, type FormEvent } from "react";
import { ArrowUp, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { BackendThreadMessageRequest, ThreadMessageSubmitReadiness, PatientContext } from "@/lib/chat-assistant";

export type ComposerSubmitState =
  | { status: "idle"; message: string }
  | { status: "blocked"; message: string }
  | { status: "loading"; message: string }
  | { status: "ready"; message: string; request: BackendThreadMessageRequest }
  | { status: "error"; message: string };

type ChatComposerProps = {
  activeContext: PatientContext | undefined;
  isSubmitting: boolean;
  onSubmitQuestion: (question: string) => ThreadMessageSubmitReadiness;
  submitState: ComposerSubmitState;
};

export function ChatComposer({ activeContext, isSubmitting, onSubmitQuestion, submitState }: ChatComposerProps) {
  const [question, setQuestion] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const scopeLabel = activeContext
    ? `${activeContext.displayLabel} / ${activeContext.permissionLabel}`
    : "No active scope selected";
  const submitDisabled = isSubmitting || !activeContext;
  const statusMessage = localError ?? submitState.message;
  const statusClassName =
    localError || submitState.status === "blocked" || submitState.status === "error"
      ? "text-[#fca5a5]"
      : submitState.status === "ready"
        ? "text-[#86efac]"
        : "text-[#9ca3af]";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setLocalError("Enter a question before submitting.");
      return;
    }

    setLocalError(null);
    const readiness = onSubmitQuestion(question);
    if (readiness.ready) {
      setQuestion("");
    }
  }

  return (
    <form className="border-t border-white/10 bg-[#0f1011] p-3 md:p-4" noValidate onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor="assistant-question">
        Ask the hospital assistant
      </label>
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 rounded-md border border-white/10 bg-[#08090a] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex min-h-10 min-w-0 flex-1 items-center gap-3">
            <Search className="size-4 shrink-0 text-[#8a8f98]" />
            <input
              aria-describedby="assistant-submit-status"
              className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-[#6f747d]"
              disabled={submitDisabled}
              id="assistant-question"
              onChange={(event) => {
                setQuestion(event.target.value);
                if (localError) {
                  setLocalError(null);
                }
              }}
              placeholder="Ask general knowledge, or select patient context first..."
              type="text"
              value={question}
            />
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button size="sm" variant="secondary" type="button">
              <ShieldCheck className="size-4" />
              <span className="max-w-[180px] truncate">{scopeLabel}</span>
            </Button>
            <Button disabled={submitDisabled} size="icon" type="submit" aria-label="Submit question">
              <ArrowUp className="size-4" />
            </Button>
          </div>
        </div>
        <p aria-live="polite" className={`text-xs ${statusClassName}`} id="assistant-submit-status">
          {isSubmitting ? "Preparing patient chat request..." : statusMessage}
        </p>
      </div>
    </form>
  );
}
