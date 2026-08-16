export function PageNavigator({
  page,
  onPageChange,
}: {
  page: number;
  onPageChange: (p: number) => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <label htmlFor="page-nav" className="text-xs font-medium text-muted-foreground whitespace-nowrap">
        Page
      </label>
      <input
        id="page-nav"
        type="number"
        value={page}
        onChange={(e) => onPageChange(Math.max(1, Number(e.target.value) || 1))}
        className="h-8 w-14 rounded-lg border border-input bg-background px-2 py-1 text-xs text-center font-medium shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        min={1}
      />
    </div>
  );
}
