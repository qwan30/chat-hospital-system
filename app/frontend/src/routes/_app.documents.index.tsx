import { createFileRoute } from "@tanstack/react-router";
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
import { FileText, Search, Sparkles, Upload } from "lucide-react";
import { documents } from "@/data/documents";

export const Route = createFileRoute("/_app/documents/")({
  head: () => ({
    meta: [
      { title: "Documents — HMS AI Copilot" },
      { name: "description", content: "Indexed documents, OCR, and semantic search." },
    ],
  }),
  component: DocumentsPage,
});

const counts = documents.reduce(
  (acc, d) => ((acc[d.status] = (acc[d.status] ?? 0) + 1), acc),
  {} as Record<string, number>,
);

function DocumentsPage() {
  return (
    <AppShell
      rightRail={
        <Card className="p-4">
          <h3 className="mb-2 text-sm font-semibold">Indexing pipeline</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center justify-between">
              <span className="text-muted-foreground">Indexed</span>
              <span className="font-semibold">{counts.indexed ?? 0}</span>
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
          <div className="mt-4 rounded-lg border bg-muted/40 p-3 text-xs text-muted-foreground">
            All uploads pass through PHI redaction before vector embedding.
          </div>
        </Card>
      }
    >
      <PageHeader
        title="Documents & OCR"
        description="Upload, index, and semantically search clinical knowledge."
        actions={
          <Button size="sm">
            <Upload className="mr-1 h-4 w-4" /> Upload documents
          </Button>
        }
      />

      <Card className="border-dashed p-8 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Upload className="h-6 w-6" />
        </div>
        <p className="mt-3 text-sm font-medium">Drag & drop PDFs, DOCX, scans, or HL7 messages</p>
        <p className="text-xs text-muted-foreground">
          Max 50MB per file · OCR runs automatically on scans
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          <Badge variant="secondary">PDF</Badge>
          <Badge variant="secondary">DOCX</Badge>
          <Badge variant="secondary">JPG/PNG (scan)</Badge>
          <Badge variant="secondary">HL7 v2</Badge>
          <Badge variant="secondary">DICOM SR</Badge>
        </div>
      </Card>

      <Card className="mt-6 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Sparkles className="h-4 w-4 text-ai" />
          <div className="relative flex-1 max-w-2xl">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              defaultValue="anticoagulation contraindications in elderly"
              className="h-10 pl-8"
              placeholder="Semantic search across the knowledge base..."
            />
          </div>
          <Button>Search</Button>
        </div>
      </Card>

      <Card className="mt-6 overflow-hidden p-0">
        <div className="flex items-center justify-between border-b p-4">
          <h3 className="text-sm font-semibold">All documents</h3>
          <span className="text-xs text-muted-foreground">{documents.length} files</span>
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
            {documents.map((d) => (
              <TableRow key={d.id}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{d.name}</span>
                  </div>
                </TableCell>
                <TableCell><Badge variant="secondary">{d.category}</Badge></TableCell>
                <TableCell className="text-sm">{d.pages || "—"}</TableCell>
                <TableCell className="text-sm">{d.size}</TableCell>
                <TableCell className="text-sm">{d.uploadedBy}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{d.uploaded}</TableCell>
                <TableCell><StatusBadge status={d.status} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </AppShell>
  );
}