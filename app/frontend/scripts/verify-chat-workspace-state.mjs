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
  assert.ok(shell.includes("onSubmitQuestion={handleSubmitQuestion}"));
  assert.ok(shell.includes("submitState={composerSubmitState}"));
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

test("patient permission states have explicit blocked and allowed copy", () => {
  const gate = source("src/components/chat/PatientContextGate.tsx");
  const mockData = source("src/lib/chat-assistant/mock-data.ts");

  assert.match(gate, /Permission pending/);
  assert.match(gate, /Patient-linked answers stay blocked until the backend confirms read access\./);
  assert.match(gate, /Permission denied/);
  assert.match(gate, /Patient-linked evidence and citations remain hidden for this context\./);
  assert.match(gate, /Permission allowed/);
  assert.match(gate, /Patient-linked answers may call the verified patient-scoped backend path\./);

  assert.match(mockData, /permissionState: "pending"/);
  assert.match(mockData, /permissionState: "denied"/);
  assert.match(mockData, /permissionState: "allowed"/);
});

test("evidence states are rendered with text labels, not color alone", () => {
  const panel = source("src/components/chat/EvidencePanel.tsx");
  const mockData = source("src/lib/chat-assistant/mock-data.ts");

  for (const label of ["Available", "Gated", "Unavailable", "No evidence"]) {
    assert.ok(panel.includes(`label: "${label}"`), `missing visible evidence label: ${label}`);
  }

  for (const state of ["available", "permission-gated", "unavailable", "no-evidence"]) {
    assert.ok(mockData.includes(`availability: "${state}"`), `missing sample evidence state: ${state}`);
  }
});

test("patient-linked sample citations are not presented as available evidence", () => {
  const mockData = source("src/lib/chat-assistant/mock-data.ts");
  const patientCitation = /id: "citation-patient-chart-gated"[\s\S]*?availability: "permission-gated"/;
  const patientEvidence = /id: "evidence-patient-chart-gated"[\s\S]*?availability: "permission-gated"/;

  assert.match(mockData, patientCitation);
  assert.match(mockData, patientEvidence);
  assert.doesNotMatch(
    mockData,
    /id: "citation-patient-chart-gated"[\s\S]*?availability: "available"/,
    "patient-linked gated citation must not be marked available",
  );
});

test("empty and unavailable evidence states have readable copy", () => {
  const panel = source("src/components/chat/EvidencePanel.tsx");
  const mockData = source("src/lib/chat-assistant/mock-data.ts");

  assert.match(panel, /No active thread evidence/);
  assert.match(panel, /has no cited evidence yet\./);
  assert.match(mockData, /Unavailable until a general-scope chat API exists\./);
  assert.match(mockData, /No source matched this part of the sample answer\./);
});

test("backend chat adapter returns matching message and evidence artifacts", () => {
  const api = source("src/lib/chat-assistant/api.ts");

  assert.match(api, /export type BackendChatArtifacts = \{\s+message: AssistantMessage;\s+evidenceSources: EvidenceSource\[\];\s+\}/);
  assert.match(api, /export function mapBackendChatResponseToChatArtifacts/);
  assert.match(api, /const evidenceSources = response\.citations\.map\(mapBackendCitationToEvidenceSource\)/);
  assert.match(api, /citations: evidenceSources\.map\(mapEvidenceSourceToCitation\)/);
});

test("backend evidence mapping preserves citation detail for the source panel", () => {
  const api = source("src/lib/chat-assistant/api.ts");
  const types = source("src/lib/chat-assistant/types.ts");

  for (const field of [
    "documentId: citation.document_id",
    "title: citation.document_title",
    "page: citation.page",
    "chunkId: citation.chunk_id",
    "excerpt: citation.content?.trim()",
    "score: citation.score",
    "metadata: citation.metadata",
  ]) {
    assert.ok(api.includes(field), `missing backend evidence field preservation: ${field}`);
  }

  assert.match(api, /evidenceSourceId: source\.id/);
  assert.match(types, /metadata: Record<string, unknown>/);
});

test("backend chat request helper rejects unsafe patient submission states", () => {
  const api = source("src/lib/chat-assistant/api.ts");

  for (const guard of [
    "context.scope !== \"patient-linked\"",
    "General hospital knowledge has no verified backend chat contract yet.",
    "context.permissionState !== \"allowed\"",
    "Patient-linked chat is blocked while permission validation is pending.",
    "Patient-linked chat is blocked because permission was denied.",
    "Patient-linked chat requires allowed permission before sending patient_id.",
    "!context.patientId",
    "Patient-linked chat requires a selected patient_id.",
    "const normalizedQuestion = question.trim();",
    "Question must include non-whitespace text before patient chat submission.",
    "!Number.isInteger(topK) || topK < 1 || topK > 20",
    "topK must be an integer between 1 and 20 before patient chat submission.",
  ]) {
    assert.ok(api.includes(guard), `missing patient chat readiness guard: ${guard}`);
  }
});

test("backend chat request helper normalizes ready requests and preserves response contracts", () => {
  const api = source("src/lib/chat-assistant/api.ts");

  for (const contract of [
    "topK = 5",
    "question: normalizedQuestion",
    "top_k: topK",
    "citations: evidenceSources.map(mapEvidenceSourceToCitation)",
    "disclaimer: response.disclaimer",
    "return \"unknown\";",
  ]) {
    assert.ok(api.includes(contract), `missing backend chat adapter contract: ${contract}`);
  }
});

test("composer uses one explicit submit path for keyboard and button activation", () => {
  const composer = source("src/components/chat/ChatComposer.tsx");

  for (const contract of [
    "onSubmit={handleSubmit}",
    "event.preventDefault();",
    "type=\"submit\"",
    "value={question}",
    "setQuestion(event.target.value)",
    "disabled={submitDisabled}",
  ]) {
    assert.ok(composer.includes(contract), `missing composer submit contract: ${contract}`);
  }

  assert.doesNotMatch(
    composer,
    /aria-label="Submit question"[\s\S]*?type="button"/,
    "submit button must not bypass the form submit path",
  );
});

test("composer readiness flow covers blocked, loading, ready, and rejected states", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");
  const composer = source("src/components/chat/ChatComposer.tsx");

  for (const contract of [
    "Enter a question before submitting.",
    "isSubmitting",
    "Preparing patient chat request...",
    "aria-live=\"polite\"",
  ]) {
    assert.ok(composer.includes(contract), `missing composer readiness contract: ${contract}`);
  }

  for (const contract of [
    "prepareVerifiedBackendChatRequest(activePatientContext, question)",
    "setComposerSubmitState({ status: \"blocked\", message: readiness.reason })",
    "setComposerSubmitState({ status: \"error\", message: readiness.reason })",
    "status: \"ready\"",
    "request: readiness.request",
    "Backend-ready patient chat request prepared.",
  ]) {
    assert.ok(shell.includes(contract), `missing shell readiness contract: ${contract}`);
  }
});

test("contract inventory reuses canonical chat type literals", () => {
  const contracts = source("src/lib/chat-assistant/contracts.ts");

  assert.match(contracts, /import type \{ ChatDataStatus, ChatScope, PatientPermissionState \} from "\.\/types";/);
  assert.ok(contracts.includes("export type ContractStatus = ChatDataStatus;"));
  assert.ok(contracts.includes("export type AssistantScope = ChatScope;"));
  assert.ok(contracts.includes("export type PermissionState = PatientPermissionState;"));

  for (const duplicate of [
    /export type ContractStatus = "verified-backend"/,
    /export type AssistantScope = "general"/,
    /export type PermissionState = "not-required"/,
  ]) {
    assert.doesNotMatch(contracts, duplicate);
  }
});
