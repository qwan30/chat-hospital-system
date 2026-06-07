"use client";

import { useAuth } from "@/lib/auth-context";
import {
  getPatientOverview,
  getPatientTimeline,
  hmsSyncPatient,
  createAccessRequest,
  ApiError,
  type PatientOverview,
  type PatientTimeline,
} from "@/lib/api-client";
import { useState, useMemo, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  Clock,
  User,
  Heart,
  ShieldCheck,
  Briefcase,
  AlertTriangle,
  RefreshCw,
  FileText,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { apiUrl, token } = useAuth();
  const opts = useMemo(() => ({ apiUrl, token }), [apiUrl, token]);

  const [overview, setOverview] = useState<PatientOverview | null>(null);
  const [timeline, setTimeline] = useState<PatientTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  // Access Request State
  const [showAccessModal, setShowAccessModal] = useState(false);
  const [justification, setJustification] = useState("");
  const [submittingAccess, setSubmittingAccess] = useState(false);
  const [accessError, setAccessError] = useState("");

  // Action states
  const [syncing, setSyncing] = useState(false);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!apiUrl || !token || !id) return;
    setLoading(true);
    setError("");
    setShowAccessModal(false);

    Promise.all([
      getPatientOverview(opts, id),
      getPatientTimeline(opts, id),
    ])
      .then(([overviewData, timelineData]) => {
        setOverview(overviewData);
        setTimeline(timelineData);
        setLoading(false);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 403) {
          setShowAccessModal(true);
        } else {
          setError(err instanceof Error ? err.message : "Failed to load patient records");
        }
        setLoading(false);
      });
  }, [apiUrl, token, id, reloadKey, opts]);
  /* eslint-enable react-hooks/set-state-in-effect */

  async function handleAccessSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (justification.length < 15) {
      setAccessError("Justification must be at least 15 characters.");
      return;
    }
    setSubmittingAccess(true);
    setAccessError("");
    try {
      await createAccessRequest(opts, id, justification);
      setShowAccessModal(false);
      setReloadKey((k) => k + 1); // trigger reload of details
    } catch (err) {
      setAccessError(err instanceof Error ? err.message : "Access request failed.");
    } finally {
      setSubmittingAccess(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    try {
      await hmsSyncPatient(opts, id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cache sync failed.");
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-[#08090a] text-white flex items-center justify-center">
        <div className="text-[#8a8f98] text-sm animate-pulse">Retrieving patient clinical profile…</div>
      </main>
    );
  }

  if (showAccessModal) {
    return (
      <main className="min-h-screen bg-[#08090a] text-white flex items-center justify-center p-6">
        <Card className="max-w-md w-full border-yellow-900/40 bg-yellow-950/10">
          <CardHeader>
            <div className="flex items-center gap-2 text-[#f59e0b]">
              <AlertTriangle className="size-5" />
              <CardTitle>Clinical Relationship Required</CardTitle>
            </div>
            <CardDescription className="text-yellow-200/70">
              You do not have active treatment relationship scopes for this patient. Enter a justification to request temporary access.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAccessSubmit} className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="justification">Access Justification (Min 15 chars)</Label>
                <Input
                  id="justification"
                  placeholder="e.g. Attending physician reviewing cardiologist notes for consult…"
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                />
              </div>
              {accessError && <p className="text-sm text-[#ffb4a8]">{accessError}</p>}
              <div className="flex gap-3 mt-4">
                <Button type="button" variant="secondary" className="flex-1" onClick={() => router.push("/patients")}>
                  Back to List
                </Button>
                <Button type="submit" className="flex-1" disabled={submittingAccess}>
                  {submittingAccess ? "Submitting…" : "Request Access"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    );
  }

  if (error || !overview) {
    return (
      <main className="min-h-screen bg-[#08090a] text-white flex items-center justify-center p-6">
        <Card className="max-w-md w-full border-red-900/40 bg-red-950/10">
          <CardHeader>
            <div className="flex items-center gap-2 text-[#ffb4a8]">
              <AlertCircle className="size-5" />
              <CardTitle>Failed to Retrieve Profile</CardTitle>
            </div>
            <CardDescription className="text-[#ffb4a8]/70">
              An error occurred while loading patient metadata.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-[#ffb4a8]/60 font-mono bg-red-950/20 p-3 rounded-md border border-red-950">
              {error || "Patient not found."}
            </p>
            <Button className="w-full" onClick={() => router.push("/patients")}>
              Return to Patient List
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#08090a] text-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-6 lg:px-8">
        <header className="flex flex-col justify-between gap-4 border-b border-white/10 pb-5 md:flex-row md:items-center">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm text-[#8a8f98]">
              <Link href="/patients" className="hover:underline text-[#8a8f98]">Patients</Link>
              <span>/</span>
              <span className="text-white font-medium">{overview.full_name}</span>
            </div>
            <h1 className="text-2xl font-medium tracking-normal md:text-3xl">{overview.full_name}</h1>
            <p className="text-xs text-[#62666d] mt-1">MRN: {overview.mrn}</p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="sm" onClick={() => setReloadKey((k) => k + 1)}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
            <Button size="sm" onClick={handleSync} disabled={syncing}>
              <RefreshCw className={`size-4 mr-1.5 ${syncing ? "animate-spin" : ""}`} />
              {syncing ? "Syncing HMS…" : "Force Cache Sync"}
            </Button>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          {/* Main workspace (AI Summary and Timeline) */}
          <div className="space-y-6">
            {/* AI Summary Card */}
            <Card className="bg-[#f7f8f8] text-[#171717]">
              <CardHeader className="border-b border-black/5 pb-4">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2 text-sm text-[#615d59]">
                    <Activity className="size-4" />
                    Notion-lite AI clinical draft
                  </div>
                  {overview.last_updated && (
                    <span className="text-xs text-[#615d59]">
                      Updated {new Date(overview.last_updated).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <CardTitle className="text-[#171717] mt-2">Clinical AI Summary</CardTitle>
                <CardDescription className="text-[#615d59]">
                  Synthesized dynamically from verified document chunks and EMR charts.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4 text-[#31302e] space-y-4 text-sm leading-6">
                {overview.ai_summary ? (
                  <p>{overview.ai_summary}</p>
                ) : (
                  <div className="py-6 text-center text-[#615d59]/70 italic bg-black/5 rounded-md">
                    No local documents indexed for patient Alice. Start clinical queries in chat or upload a document to compile clinical summaries.
                  </div>
                )}
                {overview.ai_summary && (
                  <div className="rounded-md border border-black/10 bg-white p-3 text-xs text-[#615d59] flex items-start gap-2">
                    <ShieldCheck className="size-4 text-[#27a644] flex-shrink-0 mt-0.5" />
                    <div>
                      <strong>Citations verified:</strong> Linked to vector chunk index database.
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Timeline Card */}
            <Card>
              <CardHeader>
                <CardTitle>History Timeline</CardTitle>
                <CardDescription>Chronological events from HMS and fallback indexed logs.</CardDescription>
              </CardHeader>
              <CardContent>
                {timeline?.events && timeline.events.length > 0 ? (
                  <div className="relative border-l border-white/10 ml-3 pl-6 space-y-6">
                    {timeline.events.map((event) => (
                      <div key={event.event_id} className="relative">
                        <span className="absolute -left-[31px] top-1.5 flex size-4 items-center justify-center rounded-full bg-[#0f1011] border border-white/20">
                          <span className="size-1.5 rounded-full bg-[#5e6ad2]" />
                        </span>
                        <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-1">
                          <div>
                            <h4 className="font-medium text-white text-sm">{event.title}</h4>
                            <p className="text-xs text-[#8a8f98] mt-0.5">{event.description || "No description provided."}</p>
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-[#62666d] md:self-start">
                            <Clock className="size-3.5" />
                            {new Date(event.timestamp).toLocaleDateString()}
                          </div>
                        </div>
                        <Badge className="mt-2 capitalize text-xs bg-white/[0.02]">
                          {event.event_type}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-8 text-center text-[#8a8f98] text-sm">
                    No clinical history events recorded for this patient.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Side panel (Demographics and Snapshots) */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>EMR Demographic Snapshots</CardTitle>
                <CardDescription>Patient registration records.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3 border-b border-white/5 pb-3">
                  <User className="size-5 text-[#8a8f98]" />
                  <div>
                    <div className="text-xs text-[#8a8f98]">Gender</div>
                    <div className="text-sm font-medium text-white">{overview.gender || "Unknown"}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 border-b border-white/5 pb-3">
                  <Clock className="size-5 text-[#8a8f98]" />
                  <div>
                    <div className="text-xs text-[#8a8f98]">DOB</div>
                    <div className="text-sm font-medium text-white">
                      {overview.dob ? new Date(overview.dob).toLocaleDateString() : "Unknown"}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 border-b border-white/5 pb-3">
                  <Heart className="size-5 text-[#8a8f98]" />
                  <div>
                    <div className="text-xs text-[#8a8f98]">Blood Type</div>
                    <div className="text-sm font-medium text-white">{overview.blood_type || "Unknown"}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Briefcase className="size-5 text-[#8a8f98]" />
                  <div>
                    <div className="text-xs text-[#8a8f98]">Occupation</div>
                    <div className="text-sm font-medium text-white">{overview.occupation || "Unknown"}</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Clinical Event Counts</CardTitle>
                <CardDescription>Total cached EMR records in RAG database.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4">
                <div className="bg-white/[0.02] border border-white/5 p-3 rounded-md">
                  <div className="text-xs text-[#8a8f98]">Allergies</div>
                  <div className="text-2xl font-semibold text-white mt-1">{overview.allergy_count}</div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 p-3 rounded-md">
                  <div className="text-xs text-[#8a8f98]">Prescriptions</div>
                  <div className="text-2xl font-semibold text-white mt-1">{overview.medication_count}</div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 p-3 rounded-md">
                  <div className="text-xs text-[#8a8f98]">Lab Tests</div>
                  <div className="text-2xl font-semibold text-white mt-1">{overview.lab_count}</div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 p-3 rounded-md">
                  <div className="text-xs text-[#8a8f98]">Appointments</div>
                  <div className="text-2xl font-semibold text-white mt-1">{overview.appointment_count}</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  );
}
