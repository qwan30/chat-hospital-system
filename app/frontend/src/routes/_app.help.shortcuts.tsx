import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";

export const Route = createFileRoute("/_app/help/shortcuts")({
  head: () => ({ meta: [{ title: "Keyboard shortcuts — HMS AI Copilot" }] }),
  component: ShortcutsPage,
});

const groups: { label: string; items: [string, string][] }[] = [
  {
    label: "Navigation",
    items: [
      ["⌘ K", "Open command palette"],
      ["G then D", "Go to Dashboard"],
      ["G then P", "Go to Patients"],
      ["G then C", "Go to Chat"],
      ["G then A", "Go to Audit"],
      ["?", "Show this help"],
    ],
  },
  {
    label: "Chat",
    items: [
      ["⌘ Enter", "Send message"],
      ["⌘ /", "Insert template"],
      ["⌘ Shift R", "Regenerate answer"],
      ["⌘ Shift C", "Copy with citations"],
    ],
  },
  {
    label: "Patient record",
    items: [
      ["⌘ Shift S", "Open AI summary"],
      ["[", "Previous patient"],
      ["]", "Next patient"],
      ["⌘ E", "Edit metadata (admin)"],
    ],
  },
];

function ShortcutsPage() {
  return (
    <AppShell>
      <PageHeader title="Keyboard shortcuts" description="Speed-run the copilot with these power-user shortcuts." />
      <div className="grid gap-4 md:grid-cols-2">
        {groups.map((g) => (
          <Card key={g.label} className="overflow-hidden p-0">
            <div className="border-b bg-muted/40 px-4 py-2.5 text-sm font-semibold">{g.label}</div>
            <table className="w-full text-sm">
              <tbody className="divide-y">
                {g.items.map(([k, v]) => (
                  <tr key={k}>
                    <td className="px-4 py-2.5 font-mono text-xs">{k}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}