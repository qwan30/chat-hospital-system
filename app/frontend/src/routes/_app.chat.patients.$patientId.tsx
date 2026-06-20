import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/chat/patients/$patientId")({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/chat",
      search: { patient: params.patientId },
    });
  },
});
