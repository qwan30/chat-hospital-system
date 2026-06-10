import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { FileText, Code } from "lucide-react";

interface EventDrawerProps { open: boolean; onClose: () => void; event: { id: string; timestamp: string; user: string; role: string; patient: string; action: string; resource: string; outcome: string; } | null; }

export function EventDrawer({ open, onClose, event }: EventDrawerProps) {
  if (!event) return null;
  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-[400px] sm:w-[480px]">
        <SheetHeader><SheetTitle className="text-h2">Event Details</SheetTitle></SheetHeader>
        <Tabs defaultValue="overview" className="mt-6">
          <TabsList><TabsTrigger value="overview"><FileText className="w-3.5 h-3.5 mr-1" />Overview</TabsTrigger><TabsTrigger value="raw"><Code className="w-3.5 h-3.5 mr-1" />Raw</TabsTrigger></TabsList>
          <TabsContent value="overview" className="mt-4 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {[["Event ID", event.id], ["Timestamp", event.timestamp], ["User", event.user], ["Role", event.role], ["Patient", event.patient], ["Action", event.action], ["Resource", event.resource], ["Outcome", event.outcome]].map(([k, v]) => <div key={k}><span className="text-[11px] text-text-subtle">{k}</span><p className="text-[13px] text-text-default font-medium">{v}</p></div>)}
            </div>
            <div><span className="text-[11px] text-text-subtle">Outcome</span><div className="mt-1"><Badge variant="outline" className={event.outcome === "allowed" ? "bg-success-50 text-success-600" : "bg-danger-50 text-danger-600"}>{event.outcome.toUpperCase()}</Badge></div></div>
          </TabsContent>
          <TabsContent value="raw" className="mt-4"><pre className="text-[12px] text-text-muted bg-bg-surface-tint rounded-lg p-4 overflow-x-auto font-mono">{JSON.stringify(event, null, 2)}</pre></TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
