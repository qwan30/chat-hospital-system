import { createFileRoute } from "@tanstack/react-router";
import { SsoCallback } from "@/components/hms/SsoCallbackCard";

export const Route = createFileRoute("/auth/sso/callback")({
  head: () => ({ meta: [{ title: "Signing in — HMS AI Copilot" }] }),
  component: SsoCallback,
});
