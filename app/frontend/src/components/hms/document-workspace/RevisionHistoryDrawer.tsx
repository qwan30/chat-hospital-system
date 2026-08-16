import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { History, Clock, User, CheckCircle, XCircle, FileText, Send } from "lucide-react";
import type { RevisionSetRead } from "@/lib/api/document-revisions";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

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
        <Button variant="outline" size="sm" className="h-8 gap-1.5 rounded-lg border-input bg-background/80 hover:bg-muted font-medium text-xs shadow-sm">
          <History className="h-3.5 w-3.5 text-muted-foreground" />
          History
          {revisions.length > 0 && (
            <Badge variant="secondary" className="h-5 px-1.5 text-[10px] rounded-full font-semibold">
              {revisions.length}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[500px] flex flex-col p-6">
        <SheetHeader className="pb-4 border-b">
          <SheetTitle className="text-base font-semibold flex items-center gap-2">
            <History className="h-4 w-4 text-primary" />
            Document Revision History
          </SheetTitle>
          <SheetDescription className="text-xs">
            Review past submitted edits and publication audit trail.
          </SheetDescription>
        </SheetHeader>
        <ScrollArea className="flex-1 mt-4 pr-3">
          <div className="flex flex-col gap-3">
            {revisions.map((rev) => {
              const isSelected = selectedId === rev.revision_set_id;
              return (
                <div
                  key={rev.revision_set_id}
                  className={`flex flex-col gap-2 p-3.5 border rounded-xl cursor-pointer transition-all ${
                    isSelected
                      ? "bg-primary/10 border-primary/50 ring-1 ring-primary/20 shadow-sm"
                      : "hover:bg-muted/50 border-border/80"
                  }`}
                  onClick={() => onSelect(rev.revision_set_id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-medium text-xs text-foreground">
                      <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                      Revision #{rev.revision_number}
                    </div>
                    {rev.status === "approved" && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <CheckCircle className="h-3 w-3" /> Approved
                      </span>
                    )}
                    {rev.status === "submitted" && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-700 dark:text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20">
                        <Send className="h-3 w-3" /> Submitted
                      </span>
                    )}
                    {rev.status === "rejected" && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-700 dark:text-rose-300 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                        <XCircle className="h-3 w-3" /> Rejected
                      </span>
                    )}
                    {rev.status === "pending" && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 dark:text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                        <Clock className="h-3 w-3" /> Pending
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground mt-1">
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {rev.created_by_user_id ? "Staff Clinician" : "System"}
                    </div>
                    {rev.created_at && (
                      <div>
                        {new Intl.DateTimeFormat("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        }).format(new Date(rev.created_at))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            {revisions.length === 0 && (
              <div className="text-center py-12 text-muted-foreground text-xs">
                No past revisions yet. Submit a draft to create the first revision.
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
