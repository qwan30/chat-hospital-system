export function WorkspaceToolbar({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-b bg-card/60 rounded-t-xl backdrop-blur">
      {children}
    </div>
  );
}
