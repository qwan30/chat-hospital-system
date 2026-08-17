export function RevisionSelector({
  revisions,
  selected,
  onSelect,
}: {
  revisions: any[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <label
        htmlFor="revision-select"
        className="text-xs font-medium text-muted-foreground whitespace-nowrap"
      >
        Revision
      </label>
      <select
        id="revision-select"
        aria-label="Revision"
        value={selected || ""}
        onChange={(e) => onSelect(e.target.value)}
        className="h-8 rounded-lg border border-input bg-background px-2.5 py-1 text-xs font-medium text-foreground shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring cursor-pointer"
      >
        <option value="">Draft (Working Copy)</option>
        {revisions.map((rev) => (
          <option key={rev.revision_set_id} value={rev.revision_set_id}>
            {rev.revision_set_id}
          </option>
        ))}
      </select>
    </div>
  );
}
