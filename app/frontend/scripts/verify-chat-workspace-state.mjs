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

test("AssistantShell loads persisted backend threads instead of sample conversations", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");

  for (const contract of [
    "listBackendChatThreads(apiConfig)",
    "mapBackendChatThreadToConversationThread",
    "getBackendChatThread(threadId, apiConfig)",
    "mapBackendChatThreadDetailToWorkspaceArtifacts",
    "setThreads(nextThreads)",
    "hydrateThreadDetail(preferred.id)",
    "Loaded ${nextThreads.length} persisted backend thread(s).",
  ]) {
    assert.ok(shell.includes(contract), `missing live workspace contract: ${contract}`);
  }

  assert.doesNotMatch(shell, /useState\(sampleWorkspaceState\.activeThreadId\)/);
  assert.doesNotMatch(shell, /threads=\{sampleWorkspaceState\.threads\}/);
});

test("AssistantShell exposes explicit runtime API configuration and token state", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");

  for (const contract of [
    "NEXT_PUBLIC_HOSPITAL_AI_API_BASE_URL",
    "Backend base URL",
    "Bearer token",
    "Enter a backend bearer token before loading persisted threads.",
  ]) {
    assert.ok(shell.includes(contract), `missing runtime config contract: ${contract}`);
  }

  assert.doesNotMatch(shell, /NEXT_PUBLIC_HOSPITAL_AI_DEV_TOKEN/);
  assert.doesNotMatch(shell, /localStorage/);
  assert.doesNotMatch(shell, /hospital-ai\.devToken/);
});

test("AssistantShell wires persisted thread actions into sidebar controls", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");
  const sidebar = source("src/components/chat/ConversationSidebar.tsx");
  const controls = source("src/components/chat/ThreadShareControls.tsx");

  for (const contract of [
    "createBackendChatThread",
    "updateBackendChatThread",
    "archiveBackendChatThread",
    "addBackendThreadParticipant",
    "onCreateThread={handleCreateThread}",
    "onRenameThread={handleRenameThread}",
    "onArchiveThread={handleArchiveThread}",
    "onShareThread={handleShareThread}",
  ]) {
    assert.ok(shell.includes(contract), `missing shell thread action: ${contract}`);
  }

  for (const label of [
    "Create backend conversation",
    "Rename backend conversation",
    "Share backend conversation",
    "Archive backend conversation",
  ]) {
    assert.ok(controls.includes(label), `missing action label: ${label}`);
  }

  assert.match(sidebar, /isCreatingThread: boolean/);
});

test("AssistantShell submits questions through persisted thread message API", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");
  const composer = source("src/components/chat/ChatComposer.tsx");

  for (const contract of [
    "prepareBackendThreadMessageRequest(activeThread, activePatientContext, question)",
    "askBackendThreadMessage(activeThread.id, readiness.request, apiConfig)",
    "Saving question and backend answer to the active thread.",
    "Persisted backend answer saved to this thread.",
  ]) {
    assert.ok(shell.includes(contract), `missing persisted submit contract: ${contract}`);
  }

  assert.match(composer, /ThreadMessageSubmitReadiness/);
  assert.match(composer, /BackendThreadMessageRequest/);
  assert.doesNotMatch(composer, /BackendChatRequest/);
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

test("patient permission states have explicit blocked and allowed copy", () => {
  const gate = source("src/components/chat/PatientContextGate.tsx");
  const mockData = source("src/lib/chat-assistant/mock-data.ts");

  assert.match(gate, /Permission pending/);
  assert.match(gate, /Patient-linked answers stay blocked until the backend confirms read access\./);
  assert.match(gate, /Permission denied/);
  assert.match(gate, /Patient-linked evidence and citations remain hidden for this context\./);
  assert.match(gate, /Permission allowed/);
  assert.match(gate, /Patient-linked answers may call the verified patient-scoped backend path\./);
  assert.match(gate, /General questions use backend-approved non-PHI hospital knowledge/);

  assert.match(mockData, /permissionState: "pending"/);
  assert.match(mockData, /permissionState: "denied"/);
  assert.match(mockData, /permissionState: "allowed"/);
  assert.match(mockData, /20000000-0000-0000-0000-000000000001/);
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

test("backend chat thread adapter maps persisted data into workspace artifacts", () => {
  const api = source("src/lib/chat-assistant/api.ts");
  const types = source("src/lib/chat-assistant/types.ts");

  for (const contract of [
    "export type BackendThreadWorkspaceArtifacts",
    "export function mapBackendChatThreadDetailToWorkspaceArtifacts",
    "scope,",
    "sharedState: \"backend-persisted\"",
    "participants: participants.map(mapBackendParticipantToConversationParticipant)",
    "dedupeEvidenceSources(messageArtifacts.flatMap",
    "message.scope === \"general\" ? generalKnowledgeProvenance : backendVerifiedProvenance",
  ]) {
    assert.ok(api.includes(contract), `missing adapter mapping contract: ${contract}`);
  }

  assert.match(types, /participants: ConversationParticipant\[\]/);
  assert.match(types, /accessLevel: "owner" \| "write" \| "read"/);
});

test("persisted patient contexts are derived from backend threads", () => {
  const shell = source("src/components/chat/AssistantShell.tsx");

  for (const contract of [
    "buildPatientContextsFromThreads(threads)",
    "Patient ${thread.patientContextId.slice(0, 8)} from persisted threads",
    "Backend read allowed",
    "passed participant and patient permission checks",
  ]) {
    assert.ok(shell.includes(contract), `missing derived patient context contract: ${contract}`);
  }
});

test("persisted thread readiness allows general mode and guards patient mode", () => {
  const api = source("src/lib/chat-assistant/api.ts");

  for (const contract of [
    "export function prepareBackendThreadMessageRequest",
    "thread.scope === \"general-knowledge\"",
    "Patient-linked chat is blocked while permission validation is pending.",
    "Patient-linked chat is blocked because permission was denied.",
    "context.patientId !== thread.patientContextId",
    "Question must include non-whitespace text before chat submission.",
    "topK must be an integer between 1 and 20 before chat submission.",
  ]) {
    assert.ok(api.includes(contract), `missing readiness guard: ${contract}`);
  }
});

test("general hospital knowledge is a verified backend contract", () => {
  const contracts = source("src/lib/chat-assistant/contracts.ts");
  const api = source("src/lib/chat-assistant/api.ts");

  for (const contract of [
    "general-hospital-knowledge",
    "status: \"verified-backend\"",
    "app/backend/src/hospital_ai/services/general_knowledge.py",
    "approved non-PHI knowledge sources",
  ]) {
    assert.ok(contracts.includes(contract), `missing general contract inventory item: ${contract}`);
  }

  assert.ok(api.includes("Approved general knowledge API"));
  assert.ok(api.includes("citation.metadata.approved_non_phi === true"));
});

test("backend errors are mapped to safe client messages", () => {
  const api = source("src/lib/chat-assistant/api.ts");

  for (const contract of [
    "Hospital assistant API authentication failed. Check the bearer token.",
    "Hospital assistant API access was denied for this request.",
    "Hospital assistant API is unavailable. Try again later or check backend logs.",
  ]) {
    assert.ok(api.includes(contract), `missing safe error copy: ${contract}`);
  }

  assert.doesNotMatch(api, /payload\.message \?\? payload\.detail/);
  assert.doesNotMatch(api, /detail\}/);
});

test("HMS appointment citations keep visible source lineage", () => {
  const api = source("src/lib/chat-assistant/api.ts");
  const panel = source("src/components/chat/EvidencePanel.tsx");

  for (const contract of [
    "HMS appointment evidence",
    "citation.metadata.source_system === \"hospital-management-system\"",
    "Appointment evidence is imported from the HMS appointment contract",
  ]) {
    assert.ok(api.includes(contract), `missing HMS citation lineage contract: ${contract}`);
  }

  assert.ok(panel.includes("item.metadata.source_family"));
  assert.ok(panel.includes("item.metadata.source_record_id"));
});

test("visible controls are wired actions, not inert toggles", () => {
  const sidebar = source("src/components/chat/ConversationSidebar.tsx");
  const panel = source("src/components/chat/EvidencePanel.tsx");

  assert.doesNotMatch(sidebar, /Toggle dark mode/);
  assert.doesNotMatch(sidebar, /Collapse conversation panel/);
  assert.doesNotMatch(panel, /Toggle evidence panel/);
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
    "aria-live=\"polite\"",
  ]) {
    assert.ok(composer.includes(contract), `missing composer submit contract: ${contract}`);
  }

  assert.doesNotMatch(
    composer,
    /aria-label="Submit question"[\s\S]*?type="button"/,
    "submit button must not bypass the form submit path",
  );
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
