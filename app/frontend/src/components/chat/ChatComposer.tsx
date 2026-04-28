import { ArrowUp, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ChatComposer() {
  return (
    <form className="border-t border-white/10 bg-[#0f1011] p-3 md:p-4">
      <label className="sr-only" htmlFor="assistant-question">
        Ask the hospital assistant
      </label>
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 rounded-md border border-white/10 bg-[#08090a] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:flex-row sm:items-center">
        <div className="flex min-h-10 min-w-0 flex-1 items-center gap-3">
          <Search className="size-4 shrink-0 text-[#8a8f98]" />
          <input
            className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-[#6f747d]"
            id="assistant-question"
            placeholder="Ask general knowledge, or select patient context first..."
            type="text"
          />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button size="sm" variant="secondary" type="button">
            <ShieldCheck className="size-4" />
            Scope
          </Button>
          <Button size="icon" type="button" aria-label="Submit question">
            <ArrowUp className="size-4" />
          </Button>
        </div>
      </div>
    </form>
  );
}
