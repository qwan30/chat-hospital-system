import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function PageNavigator({
  page,
  totalPages = 1,
  onPageChange,
}: {
  page: number;
  totalPages?: number;
  onPageChange: (p: number) => void;
}) {
  return (
    <div className="flex items-center gap-1 bg-background/90 border border-input rounded-lg p-0.5 shadow-sm">
      <Button
        variant="ghost"
        size="icon"
        type="button"
        disabled={page <= 1}
        onClick={() => onPageChange(Math.max(1, page - 1))}
        className="h-7 w-7 rounded-md text-muted-foreground hover:text-foreground"
        aria-label="Previous page"
      >
        <ChevronLeft className="h-3.5 w-3.5" />
      </Button>

      <div className="flex items-center gap-1 px-1 text-xs">
        <label htmlFor="page-nav" className="sr-only">
          Page
        </label>
        <input
          id="page-nav"
          aria-label="Page"
          type="number"
          value={page}
          onChange={(e) => onPageChange(Math.max(1, Number(e.target.value) || 1))}
          className="h-7 w-10 rounded border-0 bg-muted/40 px-1 py-0.5 text-xs text-center font-medium text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          min={1}
          max={totalPages > 1 ? totalPages : undefined}
        />
        {totalPages > 1 && (
          <span className="text-muted-foreground text-xs select-none">/ {totalPages}</span>
        )}
      </div>

      <Button
        variant="ghost"
        size="icon"
        type="button"
        disabled={totalPages > 1 && page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        className="h-7 w-7 rounded-md text-muted-foreground hover:text-foreground"
        aria-label="Next page"
      >
        <ChevronRight className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
