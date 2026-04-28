import { Bot, FileText, LockKeyhole, UserRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const citationChips = [
  "Policy manual p. 12",
  "Clinical workflow note",
  "Permission check",
];

export function ChatTranscript() {
  return (
    <div className="flex-1 min-w-0 overflow-y-auto px-4 py-5 md:px-5">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-5">
        <article className="max-w-3xl rounded-md border border-white/10 bg-white/[0.03] p-4">
          <div className="mb-3 flex items-center gap-2 text-sm text-[#a3a7ad]">
            <Bot className="size-4 text-[#828fff]" />
            Assistant answer
          </div>
          <p className="text-sm leading-6 text-[#e2e4e7]">
            Open into chat first. The workspace keeps answers in the center, conversation controls on the side, and
            source inspection in a dedicated evidence panel.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {citationChips.map((citation) => (
              <Badge key={citation} className="border-[#5e6ad2]/40 text-[#cfd3ff]">
                <FileText className="mr-1 size-3" />
                {citation}
              </Badge>
            ))}
          </div>
        </article>

        <article className="ml-auto max-w-2xl rounded-md border border-[#5e6ad2]/30 bg-[#5e6ad2]/10 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm text-[#cfd3ff]">
            <UserRound className="size-4" />
            Staff question
          </div>
          <p className="text-sm leading-6 text-[#eef0ff]">
            What is the ward transfer policy for a patient-linked question?
          </p>
        </article>

        <article className="max-w-3xl rounded-md border border-[#f87171]/30 bg-[#f87171]/10 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium text-[#fecaca]">
            <LockKeyhole className="size-4" />
            Patient-linked evidence remains gated
          </div>
          <p className="text-sm leading-6 text-[#f5b4b4]">
            Patient context can be selected in later story beads, but denied or pending permission states must not show
            patient evidence or citations.
          </p>
        </article>
      </div>
    </div>
  );
}
