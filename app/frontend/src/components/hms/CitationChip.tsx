import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

export function CitationChip({
  n,
  sourceId,
  className,
}: {
  n: number;
  sourceId: string;
  className?: string;
}) {
  return (
    <Link
      to="/citations/$sourceId"
      params={{ sourceId }}
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center rounded-md border border-citation/30 bg-citation/10 px-1 align-middle font-mono text-[10px] font-semibold text-citation transition hover:bg-citation/20",
        className,
      )}
    >
      [{n}]
    </Link>
  );
}