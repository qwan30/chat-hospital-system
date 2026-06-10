interface InlineCitationProps {
  id: number;
  onClick?: (id: number) => void;
}

export function InlineCitation({ id, onClick }: InlineCitationProps) {
  return (
    <button onClick={() => onClick?.(id)} className="inline-flex items-center px-1 text-[11px] font-semibold text-primary-600 bg-primary-50 rounded hover:bg-primary-100 transition-colors align-top" title={"Source " + id}>
      [{id}]
    </button>
  );
}
