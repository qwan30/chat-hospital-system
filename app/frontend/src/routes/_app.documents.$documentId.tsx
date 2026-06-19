import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { documents } from "@/data/documents";

export const Route = createFileRoute("/_app/documents/$documentId")({
  head: () => ({ meta: [{ title: "Document — HMS AI Copilot" }] }),
  component: Page,
});

function Page() {
  const { documentId } = Route.useParams();
  const d = documents.find((x) => x.id === documentId) || documents[0];
  return (
    <AppShell>
      <PageHeader
        title={d.name}
        description={`${d.category} · ${d.pages} pages · ${d.size}`}
        chips={
          <Badge variant="secondary" className="capitalize">
            {d.status}
          </Badge>
        }
        actions={
          <>
            <Button variant="outline" asChild>
              <Link to="/documents/$documentId/edit" params={{ documentId: d.id }}>
                Edit metadata
              </Link>
            </Button>
            <Button asChild>
              <Link to="/documents/$documentId/review" params={{ documentId: d.id }}>
                OCR review
              </Link>
            </Button>
          </>
        }
      />
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-2 p-5">
          <h4 className="text-sm font-semibold mb-2">Extracted text (preview)</h4>
          <pre className="whitespace-pre-wrap text-xs text-muted-foreground">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. {"\n\n"}Patient: Vance, Eleanor
            — MRN-48201{"\n"}Date: 2026-06-12{"\n\n"}Echocardiogram findings:{"\n"}• LVEF 55%{"\n"}•
            Mild left atrial dilation{"\n"}• No pericardial effusion
          </pre>
        </Card>
        <Card className="p-5 space-y-3 text-sm">
          <Row k="Uploaded" v={d.uploaded} />
          <Row k="By" v={d.uploadedBy} />
          <Row k="Type" v={d.type} />
          <Row k="OCR confidence" v="94%" />
        </Card>
      </div>
    </AppShell>
  );
}
function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{k}</span>
      <span className="font-medium">{v}</span>
    </div>
  );
}
