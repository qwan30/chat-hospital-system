"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import { searchPatients, type PatientSearchParams } from "@/lib/api/patients";
import type { Patient } from "@/lib/api-client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PatientsState } from "@/components/empty/PatientsState";
import { RecentPatientsCard } from "@/components/patient/RecentPatientsCard";
import { Search, Filter, ArrowUpDown } from "lucide-react";
import Link from "next/link";

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
        <Button variant="outline" className="gap-2">
          <Filter className="w-4 h-4" />
          Filters
        </Button>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-subtle" />
          <Input placeholder="Search by name, MRN..." value={query} onChange={(e) => setQuery(e.target.value)} className="pl-9" />
        </div>
        <Select value={department} onValueChange={setDepartment}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Department" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            <SelectItem value="Cardiology">Cardiology</SelectItem>
            <SelectItem value="Neurology">Neurology</SelectItem>
            <SelectItem value="Oncology">Oncology</SelectItem>
            <SelectItem value="Pediatrics">Pediatrics</SelectItem>
          </SelectContent>
        </Select>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-[140px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="admitted">Admitted</SelectItem>
            <SelectItem value="discharged">Discharged</SelectItem>
            <SelectItem value="observation">Observation</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {error && <Card className="border-danger-100 bg-danger-50"><CardContent className="py-6 text-center"><p className="text-danger-600 text-body-strong">Unable to load patients</p><p className="text-caption text-text-muted mt-1">{error}</p><Button variant="outline" className="mt-3" onClick={fetchPatients}>Retry</Button></CardContent></Card>}
      {loading ? <div className="space-y-3">{[1,2,3,4,5,6,7,8].map((i) => <Skeleton key={i} className="h-[64px] rounded-xl" />)}</div> : !error && patients.length === 0 ? <PatientsState /> : !error ? <div className="grid grid-cols-3 gap-4"><div className="col-span-2 space-y-2">{patients.map((p) => { const initials = p.full_name.split(" ").map((n) => n[0]).join("").toUpperCase(); return <Link key={p.id} href={"/patients/" + p.id} className="flex items-center justify-between p-4 bg-bg-surface rounded-xl border border-border-subtle hover:border-border-default hover:shadow-card transition-all group"><div className="flex items-center gap-3"><div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-[13px] font-semibold">{initials}</div><div><p className="text-[14px] font-semibold text-text-default group-hover:text-primary-600 transition-colors">{p.full_name}</p><p className="text-[12px] text-text-muted">MRN: {p.mrn}{p.department ? " · " + p.department : ""}</p></div></div><div className="flex items-center gap-3">{p.status && <Badge variant="outline" className={(p.status === "active" ? "bg-success-50 text-success-600" : p.status === "admitted" ? "bg-primary-50 text-primary-600" : "bg-bg-surface-tint text-text-muted") + " text-[11px]"}>{p.status.charAt(0).toUpperCase() + p.status.slice(1)}</Badge>}<ArrowUpDown className="w-4 h-4 text-text-subtle" /></div></Link>; })}</div><div className="space-y-4"><RecentPatientsCard patients={patients.slice(0, 5).map((p) => ({ id: p.id, fullName: p.full_name, mrn: p.mrn, department: p.department }))} /><Card><CardHeader><CardTitle className="text-h4">Quick Stats</CardTitle></CardHeader><CardContent className="space-y-3"><div className="flex items-center justify-between"><span className="text-[13px] text-text-muted">Total Patients</span><span className="text-[14px] font-semibold text-text-default">{total}</span></div><div className="flex items-center justify-between"><span className="text-[13px] text-text-muted">Showing</span><span className="text-[14px] font-semibold text-text-default">{patients.length}</span></div></CardContent></Card></div></div> : null}
    </div>
  );
}
