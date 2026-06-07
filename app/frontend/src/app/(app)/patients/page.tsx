"use client";

import { useAuth } from "@/lib/auth-context";
import { listPatients, type Patient } from "@/lib/api-client";
import { useState, useMemo } from "react";
import Link from "next/link";
import { Search, Users, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function PatientsPage() {
  const { apiUrl, token } = useAuth();
  const opts = useMemo(() => ({ apiUrl, token }), [apiUrl, token]);

  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchKey = `${apiUrl}-${token}`;
  const [lastFetchKey, setLastFetchKey] = useState("");

  if (fetchKey !== lastFetchKey && apiUrl && token) {
    setLastFetchKey(fetchKey);
    setLoading(true);
    setError("");
    listPatients(opts)
      .then((data) => {
        setPatients(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load patient records");
        setLoading(false);
      });
  }

  const filteredPatients = useMemo(() => {
    if (!searchQuery.trim()) return patients;
    const q = searchQuery.toLowerCase();
    return patients.filter(
      (p) =>
        p.full_name.toLowerCase().includes(q) ||
        p.mrn.toLowerCase().includes(q) ||
        p.department.toLowerCase().includes(q)
    );
  }, [patients, searchQuery]);

  return (
    <div style={{ padding: "1.5rem 2rem", maxWidth: 1200, margin: "0 auto" }}>
      <header style={{ display: "flex", justifyContent: "between", alignItems: "center", marginBottom: "1.5rem", borderBottom: "1px solid var(--border)", paddingBottom: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 600, color: "var(--foreground)", margin: 0 }}>
            👥 Scoped Patient Records
          </h1>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: 4 }}>
            Access clinical summaries and medical histories under authorized treatment scopes.
          </p>
        </div>
      </header>

      {/* Search Bar */}
      <div style={{ display: "flex", gap: 10, marginBottom: "1.5rem" }}>
        <div style={{ position: "relative", flex: 1 }}>
          <Search style={{ position: "absolute", left: 12, top: 11 }} className="size-4 text-[#8a8f98]" />
          <Input
            placeholder="Search patients by name, MRN, or department…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: "2.25rem" }}
          />
        </div>
        <Button variant="secondary" onClick={() => setLastFetchKey("")}>
          <RefreshCw className="size-4 mr-1.5" />
          Reload
        </Button>
      </div>

      {loading ? (
        <div style={{ color: "var(--muted)", fontSize: "0.85rem", textAlign: "center", padding: "3rem" }}>
          Retrieving authorized patient list…
        </div>
      ) : error ? (
        <Card className="border-red-900/40 bg-red-950/10">
          <CardHeader>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }} className="text-[#ffb4a8]">
              <AlertCircle className="size-5" />
              <CardTitle>Error Loading Patients</CardTitle>
            </div>
            <CardDescription className="text-[#ffb4a8]/70">
              Could not retrieve clinical permissions list from chatbot BFF.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-[#ffb4a8]/60 font-mono">{error}</p>
          </CardContent>
        </Card>
      ) : filteredPatients.length === 0 ? (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "5rem 2rem",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          textAlign: "center"
        }}>
          <Users className="size-10 text-white/20 mb-3" />
          <h2 style={{ fontSize: "1rem", fontWeight: 500, color: "var(--foreground)", margin: 0 }}>
            {searchQuery ? "No Matching Patients" : "No Patients Under Your Treatment Scope"}
          </h2>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", maxWidth: 380, marginTop: 6, marginBottom: "1.25rem" }}>
            {searchQuery
              ? "Refine your search term or clear the filter to view all scoped patient records."
              : "Ask the records administrator to establish a clinician-patient relationship or assign scopes."}
          </p>
          {searchQuery && (
            <Button variant="secondary" onClick={() => setSearchQuery("")}>
              Clear Search Filter
            </Button>
          )}
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
          {filteredPatients.map((patient) => (
            <Card key={patient.id} style={{ display: "flex", flexDirection: "column", transition: "transform 0.15s, border-color 0.15s" }} className="hover:border-white/20">
              <CardHeader style={{ paddingBottom: "0.75rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 8 }}>
                  <div>
                    <CardTitle className="text-lg text-white font-medium">{patient.full_name}</CardTitle>
                    <CardDescription className="text-xs text-[#8a8f98] mt-1">MRN: {patient.mrn}</CardDescription>
                  </div>
                  <Badge className="bg-[#5e6ad2]/10 border-[#5e6ad2]/20 text-[#828fff]">
                    {patient.department}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "between", paddingTop: 0 }}>
                <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: "1rem" }}>
                  DOB: {patient.dob ? new Date(patient.dob).toLocaleDateString() : "Unknown"}
                </div>
                <Link href={`/patients/${patient.id}`} style={{ textDecoration: "none" }}>
                  <Button className="w-full" size="sm">
                    Open Clinical Profile
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
