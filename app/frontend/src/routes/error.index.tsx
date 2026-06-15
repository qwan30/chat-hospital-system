import { createFileRoute, Link } from "@tanstack/react-router";
import { Card } from "@/components/ui/card";
import { ERRORS } from "@/lib/errors";

export const Route = createFileRoute("/error/")({
  head: () => ({ meta: [{ title: "Error catalog — HMS AI Copilot" }] }),
  component: ErrorIndex,
});

function ErrorIndex() {
  const entries = Object.values(ERRORS);
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Error catalog</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        All known error states with a live preview link. Useful for QA and design review.
      </p>
      <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
        {entries.map((e) => (
          <Card key={e.code} className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-mono uppercase text-muted-foreground">{e.http || "—"} · {e.code}</div>
                <div className="mt-0.5 text-sm font-medium">{e.title}</div>
              </div>
              <Link
                to={`/error/${e.code === "unknown" ? "server" : e.code === "route-not-found" ? "not-found" : e.code}` as never}
                className="text-xs font-medium text-primary hover:underline"
              >
                Preview →
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}