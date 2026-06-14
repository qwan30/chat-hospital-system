"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { searchPatients, type PatientSearchParams } from "@/lib/api/patients";
import type { Patient } from "@/lib/api-client";
import { PatientSearchToolbar } from "@/components/patients/PatientSearchToolbar";
import { PatientList } from "@/components/patients/PatientList";
import { QuickStatsCard } from "@/components/patients/QuickStatsCard";
import { RecentPatientsCard } from "@/components/patient/RecentPatientsCard";

export default function PatientsPage() {
  const { apiUrl, token } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [department, setDepartment] = useState("");
  const [status, setStatus] = useState("");

  const fetchPatients = useCallback(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    const params: PatientSearchParams = {};
    if (query) params.q = query;
    if (department && department !== "all") params.department = department;
    if (status && status !== "all") params.status = status;
    searchPatients({ apiUrl, token }, params)
      .then((res) => { setPatients(res.items); setTotal(res.total); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [apiUrl, token, query, department, status]);

  useEffect(() => { fetchPatients(); }, [fetchPatients]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 text-text-strong">Patients</h1>
          <p className="text-caption text-text-muted mt-1">
            {total > 0 ? total + " patient" + (total !== 1 ? "s" : "") + " found" : "Search patient records"}
          </p>
        </div>
      </div>
      <div className="grid grid-cols-[minmax(0,1fr)_392px] gap-6">
        <div className="space-y-6">
          <PatientSearchToolbar
            query={query}
            onQueryChange={setQuery}
            department={department}
            onDepartmentChange={setDepartment}
            status={status}
            onStatusChange={setStatus}
          />
          <PatientList
            patients={patients}
            loading={loading}
            error={error}
            onRetry={fetchPatients}
          />
        </div>
        <div className="space-y-4">
          <RecentPatientsCard
            patients={patients.slice(0, 5).map((p) => ({
              id: p.id,
              fullName: p.full_name,
              mrn: p.mrn,
              department: p.department,
            }))}
          />
          <QuickStatsCard total={total} showing={patients.length} />
        </div>
      </div>
    </div>
  );
}
