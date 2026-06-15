import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/error/rate-limit")({
  head: () => ({ meta: [{ title: "429 Rate limit" }] }),
  component: () => (
    <ErrorState
      code="429"
      title="Too many queries"
      description="You've exceeded the per-user query rate limit (60/min). Slow down or batch your queries; this protects the shared LLM runtime."
      tone="warning"
    />
  ),
});