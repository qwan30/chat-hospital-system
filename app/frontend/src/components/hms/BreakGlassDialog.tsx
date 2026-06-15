import { useState, type ReactNode } from "react";
import { ShieldAlert } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { logInfo } from "@/lib/log";

export function BreakGlassDialog({
  trigger,
  target,
  onConfirm,
}: {
  trigger: ReactNode;
  target: string;
  onConfirm?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const valid = reason.trim().length >= 12;

  const submit = () => {
    if (!valid) return;
    logInfo("break-glass access granted", { target, reason });
    toast.success("Break-glass access granted — event audited", {
      description: `Target: ${target}`,
    });
    setOpen(false);
    setReason("");
    onConfirm?.();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10 text-destructive">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <DialogTitle className="text-center">Break-glass access</DialogTitle>
          <DialogDescription className="text-center">
            You're requesting emergency access outside your normal scope. All actions in this
            session will be flagged and reviewed by Compliance.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="bg-reason">Clinical justification</Label>
          <Textarea
            id="bg-reason"
            placeholder="Describe the urgent clinical need (min 12 characters)…"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={4}
            maxLength={500}
          />
          <p className="text-xs text-muted-foreground">
            {reason.length}/500 · target {target}
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button variant="destructive" disabled={!valid} onClick={submit}>
            Grant emergency access
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}