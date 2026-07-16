import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/citations/$citationId")({
  head: () => ({ meta: [{ title: "Citation Details" }] }),
  component: CitationDetails,
});

function CitationDetails() {
  const { citationId } = Route.useParams();

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Citation Details</h1>
      <p>
        Viewing citation: <strong>{citationId}</strong>
      </p>
    </div>
  );
}
