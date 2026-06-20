import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/chat/general")({
  beforeLoad: () => {
    throw redirect({
      to: "/chat",
    });
  },
});
