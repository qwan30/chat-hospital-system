import { cn } from "@/lib/utils";

export function Logo({ className, size = 28 }: { className?: string; size?: number }) {
  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm",
        className,
      )}
      style={{ width: size, height: size }}
      aria-label="HMS AI Copilot"
    >
      <svg viewBox="0 0 24 24" width={size * 0.65} height={size * 0.65} fill="none">
        <path
          d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5l8-3z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="M12 8v8M8 12h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    </div>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Logo />
      <div className="flex flex-col leading-tight">
        <span className="text-sm font-semibold tracking-tight">HMS AI Copilot</span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
          Hospital Knowledge
        </span>
      </div>
    </div>
  );
}
