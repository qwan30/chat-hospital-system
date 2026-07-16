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
  fixedHeight = false,
}: {
  children: ReactNode;
  rightRail?: ReactNode;
  maxWidth?: string;
  fixedHeight?: boolean;
}) {
  return (
    <SidebarProvider>
      <div
        className={cn(
          "flex w-full bg-background",
          fixedHeight ? "h-screen overflow-hidden" : "min-h-screen",
        )}
      >
        <AppSidebar />
        <SidebarInset
          className={cn(
            "flex min-w-0 flex-1 flex-col",
            fixedHeight ? "h-screen overflow-hidden" : "",
          )}
        >
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-1.5 focus:text-xs focus:font-medium focus:text-primary-foreground"
          >
            Skip to content
          </a>
          <Topbar />
          <OfflineBanner />
          <ActingAsBanner />
          <div
            className={cn(
              "mx-auto flex w-full gap-6 px-6 py-6",
              maxWidth,
              fixedHeight ? "flex-1 overflow-hidden min-h-0" : "flex-1",
            )}
          >
            <main
              id="main-content"
              className={cn(
                "min-w-0 flex-1",
                fixedHeight ? "h-full overflow-hidden flex flex-col" : "",
              )}
            >
              {children}
            </main>
            {rightRail ? (
              <aside
                className={cn(
                  "hidden w-[340px] shrink-0 xl:block",
                  fixedHeight ? "h-full overflow-hidden" : "",
                )}
              >
                <div
                  className={cn(
                    "overflow-y-auto",
                    fixedHeight ? "h-full pb-6" : "sticky top-20 max-h-[calc(100vh-6rem)]",
                  )}
                >
                  {rightRail}
                </div>
              </aside>
            ) : null}
          </div>
          {!fixedHeight && (
            <div className={cn("mx-auto w-full px-6 pb-6", maxWidth)}>
              <SafetyFooter />
            </div>
          )}
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
