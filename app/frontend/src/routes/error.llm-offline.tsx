import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/error/llm-offline")({
  head: () => ({ meta: [{ title: "503 LLM offline" }] }),
  component: () => (
    <ErrorState
      code="503"
      title="LLM runtime is unavailable"
      description="The local Ollama runtime is restarting after a model swap. Your drafts and threads are preserved — try again in a moment, or open system health."
      cta={{ label: "View LLM health", to: "/integrations/llm" }}
      tone="critical"
    />
  ),
});