import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { RouteError } from "@/components/hms/RouteError";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/hms/StatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FileText, Search, Sparkles, Upload, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { listDocuments } from "@/lib/api/documents";
import { ErrorState } from "@/components/hms/ErrorState";
import { isDocumentReadyForRetrieval } from "@/lib/document-status";
import { useState } from "react";

export const Route = createFileRoute("/_app/documents/")({
  head: () => ({
    meta: [
      { title: "Documents — HMS AI Copilot" },
      { name: "description", content: "Indexed documents, OCR, and semantic search." },
    ],
  }),
  component: DocumentsPage,
  errorComponent: RouteError,
});

function DocumentsPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("anticoagulation contraindications in elderly");
  const [searchPatientId, setSearchPatientId] = useState("");
  const { data, isLoading, error } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments(),
  });

  const docs = data?.items || [];
  const counts = docs.reduce(
    (acc, d) => ((acc[d.status] = (acc[d.status] ?? 0) + 1), acc),
    {} as Record<string, number>,
  );
  const readyCount = docs.filter((document) => isDocumentReadyForRetrieval(document.status)).length;
  const canSearch = Boolean(searchQuery.trim() && searchPatientId.trim());

  const openPatientScopedSearch = () => {
    if (!canSearch) return;

    navigate({
      to: "/documents/search",
      search: { q: searchQuery.trim(), patientId: searchPatientId.trim() },
    });
  };

  return (
    <AppShell
      rightRail={
        isLoading || error ? undefined : (
          <Card className="p-4">
            <h3 className="mb-2 text-sm font-semibold">Indexing pipeline</h3>
            <ul className="space-y-2 text-sm">
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground">Ready</span>
                <span className="font-semibold">{readyCount}</span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground">Processing</span>
                <span className="font-semibold text-info">{counts.processing ?? 0}</span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground">OCR</span>
                <span className="font-semibold text-ai">{counts.ocr ?? 0}</span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground">Queued</span>
                <span className="font-semibold">{counts.queued ?? 0}</span>
              </li>
              <li className="flex items-center justify-between">
                <span className="text-muted-foreground">Errors</span>
                <span className="font-semibold text-destructive">{counts.error ?? 0}</span>
              </li>
            </ul>
          </Card>
        )
      }
    >
      {isLoading ? (
        <div className="flex h-[50vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="p-8">
          <ErrorState
            title="Failed to load documents"
            description={error instanceof Error ? error.message : "Unknown error"}
            code="DOC_LIST_ERR"
          />
        </div>
      ) : (
        <>
          <PageHeader
            title="Documents & OCR"
            description="Upload, index, and semantically search clinical knowledge."
            actions={
              <Button size="sm" asChild>
                <Link to="/documents/upload">
                  <Upload className="mr-1 h-4 w-4" /> Upload documents
                </Link>
              </Button>
            }
          />

          <Card className="border-dashed p-8 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Upload className="h-6 w-6" />
            </div>
            <p className="mt-3 text-sm font-medium">
              Drag & drop PDFs, DOCX, scans, or HL7 messages
            </p>
            <p className="text-xs text-muted-foreground">
              Max 50MB per file · OCR runs automatically on scans
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              <Badge variant="secondary">PDF</Badge>
              <Badge variant="secondary">DOCX</Badge>
              <Badge variant="secondary">JPG/PNG (scan)</Badge>
              <Badge variant="secondary">HL7 v2</Badge>
            </div>
          </Card>

          <Card className="mt-6 p-4">
            <div className="flex flex-wrap items-center gap-3">
              <Sparkles className="h-4 w-4 text-ai" />
              <Input
                value={searchPatientId}
                onChange={(e) => setSearchPatientId(e.target.value)}
                className="h-10 w-full sm:w-64"
                placeholder="Patient UUID (required)"
                aria-label="Patient UUID"
              />
              <div className="relative flex-1 max-w-2xl">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      openPatientScopedSearch();
                    }
                  }}
                  className="h-10 pl-8"
                  placeholder="Search this patient's documents..."
                />
              </div>
              <Button onClick={openPatientScopedSearch} disabled={!canSearch}>
                Search
              </Button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Search is limited to the selected patient's authorized documents.
            </p>
          </Card>

          <Card className="mt-6 overflow-hidden p-0">
            <div className="flex items-center justify-between border-b p-4">
              <h3 className="text-sm font-semibold">All documents</h3>
              <span className="text-xs text-muted-foreground">{docs.length} files</span>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Pages</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Uploaded by</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {docs.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell>
                      <Link
                        to="/documents/$documentId"
                        params={{ documentId: d.id }}
                        className="flex items-center gap-2 hover:underline"
                      >
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{d.title}</span>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{d.document_type}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">{d.page_count || "—"}</TableCell>
                    <TableCell className="text-sm">—</TableCell>
                    <TableCell className="text-sm font-mono" title={d.uploaded_by}>
                      {d.uploaded_by.substring(0, 8)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(d.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={d.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </>
      )}
    </AppShell>
  );
}
