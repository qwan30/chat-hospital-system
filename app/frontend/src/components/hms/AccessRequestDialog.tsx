import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { ShieldCheck } from "lucide-react";

export function AccessRequestDialog({
  patientName,
  trigger,
}: {
  patientName: string;
  trigger: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <DialogTitle>Request access to patient record</DialogTitle>
          <DialogDescription>
            Provide a clinical justification. All access requests are audit-logged and reviewed by
            the patient's care team.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              Patient
            </Label>
            <p className="mt-1 text-sm font-medium">{patientName}</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="purpose">Purpose</Label>
            <Select defaultValue="consult">
              <SelectTrigger id="purpose">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="consult">Clinical consult</SelectItem>
                <SelectItem value="emergency">Emergency / break-glass</SelectItem>
                <SelectItem value="research">IRB-approved research</SelectItem>
                <SelectItem value="billing">Billing & coding</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="justification">Clinical justification</Label>
            <Textarea
              id="justification"
              rows={4}
              placeholder="e.g. Requested second opinion on cardiac imaging from primary care."
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              toast.success("Access request submitted", {
                description: "Audit event logged. You will be notified within 15 minutes.",
              });
              setOpen(false);
            }}
          >
            Submit request
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
