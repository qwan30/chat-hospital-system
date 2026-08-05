export function PageNavigator({ 
  page, 
  onPageChange 
}: { 
  page: number, 
  onPageChange: (p: number) => void 
}) {
  return (
    <div className="flex items-center gap-2">
      <label htmlFor="page-nav" className="text-sm font-medium">Page</label>
      <input 
        id="page-nav"
        type="number" 
        value={page} 
        onChange={(e) => onPageChange(Number(e.target.value))} 
        className="w-16 p-1 border rounded"
        min={1}
      />
    </div>
  );
}
