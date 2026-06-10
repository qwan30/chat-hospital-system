"use client";

import { useState, use } from "react";
import { useAuth } from "@/lib/auth-context";
import { createAccessRequest } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ContextChip } from "@/components/patient/ContextChip";
import { Shield, Clock, UserCheck, Bell, Lock, AlertTriangle, ChevronRight, CheckCircle } from "lucide-react";

export default function AccessDeniedPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { apiUrl, token } = useAuth();
  const [showRequest, setShowRequest] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [requested, setRequested] = useState(false);
  const [form, setForm] = useState({ duration: "4h", urgency: "routine", relationship: "attending", purpose: "immediate_care", justification: "" });

  const handleSubmit = async () => {
    if (!apiUrl || !token) return;
    setSubmitting(true);
    try {
      await createAccessRequest({ apiUrl, token }, { patient_id: id, resource: "full_record", duration: form.duration, urgency: form.urgency, relationship: form.relationship, purpose: form.purpose, justification: form.justification });
      setRequested(true);
      setShowRequest(false);
    } catch {}
    finally { setSubmitting(false); }
  };

  return (
    <div className="p-6 space-y-6">
      <ContextChip fullName="Jonathan Blake" mrn="MRN-2025-0847" permission="denied" />
      <Card className="border-danger-100">
        <CardContent className="py-10 text-center">
          <div className="w-16 h-16 rounded-2xl bg-danger-50 flex items-center justify-center mx-auto mb-5"><Shield className="w-8 h-8 text-danger-500" /></div>
          <h1 className="text-h1 text-text-strong mb-2">Access Denied</h1>
          <p className="text-body text-text-muted max-w-lg mx-auto mb-2">You do not have permission to view this patient record.</p>
          <p className="text-[12px] text-text-subtle max-w-md mx-auto mb-8">Reason: ABAC policy requires a direct care relationship.</p>
          {requested ? (
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-success-50 text-success-600 rounded-lg text-[14px] font-medium"><CheckCircle className="w-4 h-4" />Access Request Submitted</div>
          ) : (
            <Dialog open={showRequest} onOpenChange={setShowRequest}>
              <DialogTrigger asChild><Button className="gap-2"><Lock className="w-4 h-4" />Request Emergency Access</Button></DialogTrigger>
              <DialogContent className="sm:max-w-[560px]">
                <DialogHeader><DialogTitle className="text-h2">Request Access</DialogTitle></DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="flex items-center gap-3 p-3 bg-bg-surface-tint rounded-lg"><Shield className="w-5 h-5 text-primary-500" /><div><p className="text-[13px] font-medium text-text-default">Jonathan Blake</p><p className="text-[11px] text-text-muted">MRN-2025-0847</p></div></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2"><Label className="text-[12px]">Duration</Label><Select value={form.duration} onValueChange={(v) => setForm((f) => ({ ...f, duration: v }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="1h">1 hour</SelectItem><SelectItem value="4h">4 hours</SelectItem><SelectItem value="8h">8 hours</SelectItem><SelectItem value="24h">24 hours</SelectItem></SelectContent></Select></div>
                    <div className="space-y-2"><Label className="text-[12px]">Urgency</Label><Select value={form.urgency} onValueChange={(v) => setForm((f) => ({ ...f, urgency: v }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="routine">Routine</SelectItem><SelectItem value="urgent">Urgent</SelectItem><SelectItem value="emergency">Emergency</SelectItem></SelectContent></Select></div>
                    <div className="space-y-2"><Label className="text-[12px]">Relationship</Label><Select value={form.relationship} onValueChange={(v) => setForm((f) => ({ ...f, relationship: v }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="attending">Attending</SelectItem><SelectItem value="consulting">Consulting</SelectItem><SelectItem value="covering">Covering</SelectItem><SelectItem value="emergency">Emergency Dept</SelectItem></SelectContent></Select></div>
                    <div className="space-y-2"><Label className="text-[12px]">Purpose</Label><Select value={form.purpose} onValueChange={(v) => setForm((f) => ({ ...f, purpose: v }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="immediate_care">Immediate Care</SelectItem><SelectItem value="care_coordination">Care Coordination</SelectItem><SelectItem value="records_review">Records Review</SelectItem></SelectContent></Select></div>
                  </div>
                  <div className="space-y-2"><Label className="text-[12px]">Clinical Justification</Label><Textarea placeholder="Describe why access is clinically necessary..." value={form.justification} onChange={(e) => setForm((f) => ({ ...f, justification: e.target.value }))} className="min-h-[80px]" maxLength={500} /><p className="text-[11px] text-text-subtle text-right">{form.justification.length}/500</p></div>
                  <div className="flex items-start gap-2 p-3 rounded-lg bg-warning-50 border border-warning-100"><AlertTriangle className="w-4 h-4 text-warning-500 flex-shrink-0 mt-0.5" /><p className="text-[12px] text-warning-700">All emergency access requests are logged and audited.</p></div>
                  <div className="flex justify-end gap-3 pt-2"><Button variant="outline" onClick={() => setShowRequest(false)}>Cancel</Button><Button onClick={handleSubmit} disabled={!form.justification || submitting}>{submitting ? "Submitting..." : "Submit Request"}</Button></div>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-4">
        <Card><CardContent className="p-5"><h3 className="text-h4 text-text-strong mb-4">What You Can Do</h3><div className="space-y-3"><div className="flex items-start gap-3"><Lock className="w-4 h-4 text-text-subtle mt-0.5" /><p className="text-[13px] text-text-default">Request emergency access with clinical justification</p></div><div className="flex items-start gap-3"><Clock className="w-4 h-4 text-text-subtle mt-0.5" /><p className="text-[13px] text-text-default">Wait for approved care relationship</p></div><div className="flex items-start gap-3"><Bell className="w-4 h-4 text-text-subtle mt-0.5" /><p className="text-[13px] text-text-default">Notify the attending physician</p></div></div></CardContent></Card>
        <Card><CardContent className="p-5"><h3 className="text-h4 text-text-strong mb-4">Why Access Is Blocked</h3><div className="space-y-2"><div className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-text-subtle" /><p className="text-[13px] text-text-muted">No active care relationship</p></div><div className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-text-subtle" /><p className="text-[13px] text-text-muted">Patient record sensitivity: Standard</p></div><div className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-text-subtle" /><p className="text-[13px] text-text-muted">ABAC policy: direct_care_required</p></div></div></CardContent></Card>
      </div>
    </div>
  );
}
