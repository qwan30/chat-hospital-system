"use client";

import { ShieldCheck } from "lucide-react";
import { PRODUCT_NAME } from "@/lib/constants";

type BrandLockupProps = {
  variant?: "sidebar" | "topbar" | "auth";
  showSubtitle?: boolean;
};

const SIZES = {
  sidebar: { tile: "size-10", logo: "size-8", title: "text-[14px] font-semibold", subtitle: "text-[11px]" },
  topbar: { tile: "size-9", logo: "size-7", title: "text-[16px] font-semibold", subtitle: "hidden" },
  auth: { tile: "size-[60px]", logo: "size-10", title: "text-h3", subtitle: "text-body text-text-muted" },
} as const;

export function BrandLockup({ variant = "sidebar", showSubtitle = variant === "sidebar" }: BrandLockupProps) {
  const s = SIZES[variant];
  const title = variant === "topbar" ? PRODUCT_NAME : "Hospital AI";
  const subtitle = "Knowledge Assistant";

  return (
    <div
      className="flex items-center gap-3"
      role="banner"
      aria-label={variant === "topbar" ? PRODUCT_NAME : "Hospital AI — Knowledge Assistant"}
    >
      {/* Logo tile */}
      <div className={`${s.tile} grid place-items-center rounded-lg bg-white shadow-sm ring-1 ring-border-default flex-shrink-0`}>
        <img
          src="/images/logo.png"
          alt=""
          className={`${s.logo} object-contain`}
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.style.display = "none";
            const fallback = target.nextElementSibling as HTMLElement | null;
            if (fallback) fallback.classList.remove("hidden");
          }}
        />
        <span className="hidden"><ShieldCheck className={s.logo} /></span>
      </div>

      {/* Text */}
      <div className="min-w-0">
        <p className={`truncate leading-5 text-strong ${s.title}`}>{title}</p>
        {showSubtitle && (
          <p className={`truncate leading-4 text-muted ${s.subtitle}`}>{subtitle}</p>
        )}
      </div>
    </div>
  );
}
