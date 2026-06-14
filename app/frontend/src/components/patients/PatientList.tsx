"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PatientsState } from "@/components/empty/PatientsState";
import { PatientListRow } from "@/components/patients/PatientListRow";

export interface PatientListPatient {
  id: string;
  full_name: string;
  mrn: string;
  department?: string;
  status?: string;
}

export interface PatientListProps {
  patients: PatientListPatient[];
  loading: boolean;
  error: string;
  onRetry: () => void;
}

export function PatientList({
  patients,
  loading,
  error,
  onRetry,
}: PatientListProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <Skeleton key={i} className="h-[64px] rounded-xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-danger-100 bg-danger-50">
        <CardContent className="py-6 text-center">
          <p className="text-danger-600 text-body-strong">
            Unable to load patients
          </p>
          <p className="text-caption text-text-muted mt-1">{error}</p>
          <Button variant="outline" className="mt-3" onClick={onRetry}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (patients.length === 0) {
    return <PatientsState />;
  }

  return (
    <div className="space-y-2">
      {patients.map((p) => (
        <PatientListRow
          key={p.id}
          id={p.id}
          fullName={p.full_name}
          mrn={p.mrn}
          department={p.department}
          status={p.status}
        />
      ))}
    </div>
  );
}
