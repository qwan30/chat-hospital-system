import { createFileRoute } from "@tanstack/react-router";
import { ErrorState } from "@/components/hms/ErrorState";

export const Route = createFileRoute("/error/authentication-required")({
  head: () => ({ meta: [{ title: "401 Authentication required" }] }),
  component: () => (
    <ErrorState
      code="401"
      title="Authentication required"
      description="This action requires a valid clinical session. Your bearer token is missing or has expired. Sign in again to continue — your draft is preserved."
      cta={{ label: "Sign in", to: "/auth/login" }}
      tone="info"
    />
  ),
});