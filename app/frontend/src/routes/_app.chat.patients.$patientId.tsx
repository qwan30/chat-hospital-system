import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/chat/patients/$patientId")({
  beforeLoad: ({ params, search }) => {
    throw redirect({
      to: "/chat",
      search: { ...search, patient: params.patientId },
    });
  },
});
