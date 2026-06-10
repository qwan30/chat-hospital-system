import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Shield, AlertTriangle } from "lucide-react";
import { useState } from "react";

interface RequestModalProps {
  open: boolean;
  onClose: () => void;
  patientName: string;
  mrn: string;
  onSubmit: (data: { duration: string; urgency: string; relationship: string; purpose: string; justification: string }) => void;
}

export function RequestModal({ open, onClose, patientName, mrn, onSubmit }: RequestModalProps) {
  const [form, setForm] = useState({ duration: "4h", urgency: "routine", relationship: "attending", purpose: "immediate_care", justification: "" });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    await onSubmit(form);
    setSubmitting(false);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[540px]">
        <DialogHeader><DialogTitle>Request Emergency Access</DialogTitle></DialogHeader>
        <div className="space-y-4 mt-4">
          <div className="flex items-center gap-3 p-3 bg-bg-surface-tint rounded-lg"><Shield className="w-5 h-5 text-primary-500" /><div><p className="text-[13px] font-medium">{patientName}</p><p className="text-[11px] text-text-muted">MRN: {mrn}</p></div></div>
          <div className="grid grid-cols-2 gap-4">
            <div><Label className="text-[12px]">Duration</Label><Select value={form.duration} onValueChange={(v) => setForm((f) => ({ ...f, duration: v }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="1h">1 hour</SelectItem><SelectItem value="4h">4 hours</SelectItem><SelectItem value="8h">8 hours</SelectItem><SelectItem value="24h">24 hours</SelectItem></SelectContent></Select></div>
            <div><Label className="text-[12px]">Urgency</Label><Select value={form.urgency} onValueChange={(v) => setForm((f) => ({ ...f, urgency: v }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="routine">Routine</SelectItem><SelectItem value="urgent">Urgent</SelectItem><SelectItem value="emergency">Emergency</SelectItem></SelectContent></Select></div>
          </div>
          <div><Label className="text-[12px]">Justification</Label><Textarea value={form.justification} onChange={(e) => setForm((f) => ({ ...f, justification: e.target.value }))} className="min-h-[80px]" maxLength={500} /><p className="text-[11px] text-text-subtle text-right">{form.justification.length}/500</p></div>
          <div className="flex items-start gap-2 p-3 rounded-lg bg-warning-50 border border-warning-100"><AlertTriangle className="w-4 h-4 text-warning-500 mt-0.5" /><p className="text-[12px] text-warning-700">All access requests are logged and audited.</p></div>
          <div className="flex justify-end gap-3"><Button variant="outline" onClick={onClose}>Cancel</Button><Button onClick={handleSubmit} disabled={!form.justification || submitting}>{submitting ? "Submitting..." : "Submit"}</Button></div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
