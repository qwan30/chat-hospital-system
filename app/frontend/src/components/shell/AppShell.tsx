import type { ReactNode } from "react";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import { Topbar } from "./Topbar";
import { ActingAsBanner } from "./ActingAsBanner";
import { OfflineBanner } from "./OfflineBanner";
import { SafetyFooter } from "@/components/hms/SafetyFooter";
import { cn } from "@/lib/utils";

export function AppShell({
  children,
  rightRail,
  maxWidth = "max-w-[1400px]",
}: {
  children: ReactNode;
  rightRail?: ReactNode;
  maxWidth?: string;
}) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-background">
        <AppSidebar />
        <SidebarInset className="flex min-w-0 flex-1 flex-col">
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-1.5 focus:text-xs focus:font-medium focus:text-primary-foreground"
          >
            Skip to content
          </a>
          <Topbar />
          <OfflineBanner />
          <ActingAsBanner />
          <div className={cn("mx-auto flex w-full flex-1 gap-6 px-6 py-6", maxWidth)}>
            <main id="main-content" className="min-w-0 flex-1">{children}</main>
            {rightRail ? (
              <aside className="hidden w-[340px] shrink-0 xl:block">
                <div className="sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto">
                  {rightRail}
                </div>
              </aside>
            ) : null}
          </div>
          <div className={cn("mx-auto w-full px-6 pb-6", maxWidth)}>
            <SafetyFooter />
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}