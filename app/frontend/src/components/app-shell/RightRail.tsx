import { cn } from "@/lib/utils";

interface RightRailProps {
  children: React.ReactNode;
  className?: string;
  width?: number;
}

export function RightRail({ children, className, width = 300 }: RightRailProps) {
  return (
    <aside
      className={cn("flex flex-col gap-4 flex-shrink-0 overflow-y-auto", className)}
      style={{ width }}
    >
      {children}
    </aside>
  );
}
