import * as React from "react";
import { cn } from "@/lib/utils";

function Input({ className, type, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type={type}
      className={cn(
        "h-9 w-full rounded-md border border-white/10 bg-white/[0.03] px-3 text-sm text-white outline-none transition placeholder:text-[#62666d] focus:border-[#7170ff]",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
