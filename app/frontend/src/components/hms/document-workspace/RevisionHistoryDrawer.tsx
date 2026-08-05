import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { History, Clock, User, CheckCircle, XCircle, FileText } from "lucide-react";
import { RevisionSetRead } from "@/lib/api/types";
import { ScrollArea } from "@/components/ui/scroll-area";

export function RevisionHistoryDrawer({
  revisions,
  selectedId,
  onSelect,
}: {
  revisions: RevisionSetRead[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <History className="h-4 w-4" />
          History
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Revision History</SheetTitle>
          <SheetDescription>
            View past edits and status changes for this document.
          </SheetDescription>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-120px)] mt-4">
          <div className="flex flex-col gap-4 pr-4">
            {revisions.map((rev) => (
              <div
                key={rev.revision_set_id}
                className={`flex flex-col gap-2 p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedId === rev.revision_set_id
                    ? "bg-primary/10 border-primary"
                    : "hover:bg-muted"
                }`}
                onClick={() => onSelect(rev.revision_set_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-medium">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    Revision #{rev.revision_number}
                  </div>
                  {rev.status === "approved" && (
                    <span className="flex items-center gap-1 text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">
                      <CheckCircle className="h-3 w-3" /> Approved
                    </span>
                  )}
                  {rev.status === "rejected" && (
                    <span className="flex items-center gap-1 text-xs text-red-600 bg-red-100 px-2 py-1 rounded-full">
                      <XCircle className="h-3 w-3" /> Rejected
                    </span>
                  )}
                  {rev.status === "pending" && (
                    <span className="flex items-center gap-1 text-xs text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full">
                      <Clock className="h-3 w-3" /> Pending
                    </span>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground mt-2">
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {rev.created_by_user_id || "System"}
                  </div>
                  {rev.created_at && (
                    <div className="flex items-center gap-1 text-right justify-end">
                      {new Intl.DateTimeFormat('en-US', {
                        month: 'short', day: 'numeric', year: 'numeric',
                        hour: 'numeric', minute: 'numeric'
                      }).format(new Date(rev.created_at))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {revisions.length === 0 && (
              <div className="text-center p-8 text-muted-foreground">
                No history available for this document.
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
