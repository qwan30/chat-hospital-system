import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPatient } from "@/lib/api/patients";
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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { UserPlus } from "lucide-react";

export function AddPatientDialog({ trigger }: { trigger: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [fullName, setFullName] = useState("");
  const [dob, setDob] = useState("");
  const [department, setDepartment] = useState("Cardiology");
  const [status, setStatus] = useState("stable");

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: createPatient,
    onSuccess: (data) => {
      toast.success("Patient added successfully", {
        description: `Patient ${data.full_name} (${data.mrn}) created in database.`,
      });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      setOpen(false);
      setFullName("");
      setDob("");
      setDepartment("Cardiology");
      setStatus("stable");
    },
    onError: (err: Error) => {
      toast.error("Failed to add patient", { description: err.message });
    },
  });

  const handleSubmit = () => {
    if (!fullName.trim()) {
      toast.error("Full name is required");
      return;
    }
    // Generate a random MRN-XXXXX
    const randomDigits = Math.floor(10000 + Math.random() * 90000);
    const mrn = `MRN-${randomDigits}`;

    mutation.mutate({
      full_name: fullName,
      dob: dob || null,
      department: department,
      status: status,
      mrn: mrn,
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <UserPlus className="h-5 w-5" />
          </div>
          <DialogTitle>Add New Patient</DialogTitle>
          <DialogDescription>
            Register a new patient in the hospital knowledge system.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="fullName">Full Name</Label>
            <Input
              id="fullName"
              placeholder="e.g. John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="dob">Date of Birth</Label>
            <Input
              id="dob"
              type="date"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="department">Department</Label>
            <Select value={department} onValueChange={setDepartment} disabled={mutation.isPending}>
              <SelectTrigger id="department">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Cardiology">Cardiology</SelectItem>
                <SelectItem value="ICU">ICU</SelectItem>
                <SelectItem value="Internal Medicine">Internal Medicine</SelectItem>
                <SelectItem value="Emergency">Emergency</SelectItem>
                <SelectItem value="Pharmacy">Pharmacy</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="status">Clinical Status</Label>
            <Select value={status} onValueChange={setStatus} disabled={mutation.isPending}>
              <SelectTrigger id="status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="stable">Stable</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="watch">Watch</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter className="mt-4">
          <Button variant="ghost" onClick={() => setOpen(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={mutation.isPending}>
            {mutation.isPending ? "Adding..." : "Add Patient"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
