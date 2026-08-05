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
    <div className="flex items-center gap-2">
      <label htmlFor="revision-select" className="text-sm font-medium">
        Revision
      </label>
      <select
        id="revision-select"
        aria-label="Revision"
        value={selected || ""}
        onChange={(e) => onSelect(e.target.value)}
        className="p-1 border rounded"
      >
        <option value="" disabled>
          Select revision
        </option>
        {revisions.map((rev) => (
          <option key={rev.revision_set_id} value={rev.revision_set_id}>
            {rev.revision_set_id}
          </option>
        ))}
      </select>
    </div>
  );
}
