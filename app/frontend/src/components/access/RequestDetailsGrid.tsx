export function RequestDetailsGrid({ details }: { details: { label: string; value: string }[] }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {details.map((d) => <div key={d.label}><span className="text-[11px] text-text-subtle">{d.label}</span><p className="text-[13px] text-text-default font-medium">{d.value}</p></div>)}
    </div>
  );
}
