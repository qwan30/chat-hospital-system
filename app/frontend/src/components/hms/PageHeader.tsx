import type { ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

export function PageHeader({
  title,
  description,
  actions,
  chips,
  backLink,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  chips?: ReactNode;
  backLink?: { to: string; label?: string };
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        {backLink && (
          <Link
            to={backLink.to}
            className="mb-2 inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            {backLink.label || "Back"}
          </Link>
        )}
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
        {chips ? <div className="mt-3 flex flex-wrap items-center gap-2">{chips}</div> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
