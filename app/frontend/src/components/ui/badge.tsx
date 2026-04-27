import * as React from "react";
import { cn } from "@/lib/utils";

function Badge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs font-medium text-[#d0d6e0]",
        className,
      )}
      {...props}
    />
  );
}

export { Badge };
