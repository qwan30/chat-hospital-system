import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const appRoot = join(root, "..");

function source(relativePath) {
  return readFileSync(join(appRoot, relativePath), "utf8");
}

test("AssistantShell owns the active workspace model", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");

  assert.match(shell, /useState\(sampleWorkspaceState\.activeThreadId\)/);
  assert.match(shell, /useState\(sampleWorkspaceState\.activePatientContextId\)/);
  assert.match(shell, /function handleSelectThread\(threadId: string\)/);
  assert.match(shell, /setActivePatientContextId\(nextThread\.patientContextId \?\?/);
  assert.match(shell, /const activeEvidenceSources = useMemo/);
});

test("AssistantShell wires one active model into all chat workspace children", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");

  assert.ok(shell.includes("activeThread={activeThread}"));
  assert.ok(shell.includes("activeThreadId={activeThreadId}"));
  assert.ok(shell.includes("onSelectThread={handleSelectThread}"));
  assert.ok(shell.includes("activeContext={activePatientContext}"));
  assert.ok(shell.includes("activeContextId={activePatientContextId}"));
  assert.ok(shell.includes("onSelectContext={setActivePatientContextId}"));
  assert.ok(shell.includes("evidenceSources={activeEvidenceSources}"));
});

test("child workspace components do not own disconnected sample workspace state", () => {
  const childFiles = [
    "src/components/chat/ConversationSidebar.tsx",
    "src/components/chat/ChatTranscript.tsx",
    "src/components/chat/PatientContextGate.tsx",
    "src/components/chat/EvidencePanel.tsx",
    "src/components/chat/ChatComposer.tsx",
  ];

  for (const file of childFiles) {
    const content = source(file);

    assert.doesNotMatch(content, /sampleWorkspaceState/);
  }
});

test("sidebar, transcript, context gate, composer, and evidence panel receive explicit props", () => {
  assert.match(source("src/components/chat/ConversationSidebar.tsx"), /onSelectThread: \(threadId: string\) => void/);
  assert.match(source("src/components/chat/ChatTranscript.tsx"), /activeThread: ConversationThread \| undefined/);
  assert.match(source("src/components/chat/PatientContextGate.tsx"), /onSelectContext: \(contextId: string\) => void/);
  assert.match(source("src/components/chat/ChatComposer.tsx"), /activeContext: PatientContext \| undefined/);
  assert.match(source("src/components/chat/EvidencePanel.tsx"), /evidenceSources: EvidenceSource\[\]/);
});
