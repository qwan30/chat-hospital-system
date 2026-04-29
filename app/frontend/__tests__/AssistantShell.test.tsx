/**
 * Integration tests for the AssistantShell chat component.
 *
 * Verifies the user-visible flow:
 *   1. Renders correctly with header, sidebar, and chat elements
 *   2. After entering a token & refreshing, workspace loads threads
 *   3. Submit a question triggers streamChat
 *   4. Stop-generating button appears during streaming
 *   5. Patient-linked evidence gate notice is visible
 *
 * All network calls are mocked — no backend required.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// ── Mock the barrel module that AssistantShell imports from ─────────────

const mockListThreads = vi.fn();
const mockGetThread = vi.fn();
const mockCreateThread = vi.fn();
const mockUpdateThread = vi.fn();
const mockArchiveThread = vi.fn();
const mockAddParticipant = vi.fn();
const mockPrepareRequest = vi.fn();
const mockStreamChat = vi.fn();

vi.mock("@/lib/chat-assistant", () => {
  const generalContext = {
    id: "general-knowledge",
    scope: "general-knowledge",
    patientId: null,
    displayLabel: "General Knowledge",
    permissionState: "not-required",
    permissionLabel: "No patient scope",
    provenance: {
      status: "verified-backend",
      visibleLabel: "System",
      sourceLabel: "Default",
      note: "",
    },
  };

  return {
    listBackendChatThreads: (...args: unknown[]) => mockListThreads(...args),
    getBackendChatThread: (...args: unknown[]) => mockGetThread(...args),
    createBackendChatThread: (...args: unknown[]) => mockCreateThread(...args),
    updateBackendChatThread: (...args: unknown[]) => mockUpdateThread(...args),
    archiveBackendChatThread: (...args: unknown[]) => mockArchiveThread(...args),
    addBackendThreadParticipant: (...args: unknown[]) => mockAddParticipant(...args),
    prepareBackendThreadMessageRequest: (...args: unknown[]) => mockPrepareRequest(...args),
    mapBackendChatThreadToConversationThread: vi.fn().mockImplementation((t: { id: string; title: string }) => ({
      id: t.id,
      title: t.title,
      description: "Backend thread",
      scope: "general-knowledge",
      active: true,
      sharedState: "backend-persisted",
      updatedAt: "2026-01-01T00:00:00Z",
      messages: [],
      patientContextId: null,
      participants: [],
      provenance: {
        status: "verified-backend",
        visibleLabel: "Backend",
        sourceLabel: "Test",
        note: "",
      },
    })),
    mapBackendChatThreadDetailToWorkspaceArtifacts: vi.fn().mockImplementation(
      (detail: { id: string; title: string }) => ({
        thread: {
          id: detail.id,
          title: detail.title,
          description: "Backend thread",
          scope: "general-knowledge",
          active: true,
          sharedState: "backend-persisted",
          updatedAt: "2026-01-01T00:00:00Z",
          messages: [],
          patientContextId: null,
          participants: [],
          provenance: {
            status: "verified-backend",
            visibleLabel: "Backend",
            sourceLabel: "Test",
            note: "",
          },
        },
        evidenceSources: [],
      }),
    ),
    sampleWorkspaceState: {
      threads: [],
      patientContexts: [generalContext],
      evidenceSources: [],
      activeThreadId: "",
      activePatientContextId: "general-knowledge",
    },
  };
});

vi.mock("@/lib/chat-assistant/stream-client", () => ({
  streamChat: (...args: unknown[]) => mockStreamChat(...args),
}));

// Import after mocks
import { AssistantShell } from "@/components/chat/AssistantShell";

// ── Test helpers ───────────────────────────────────────────────────────

function setupDefaultMocks() {
  mockListThreads.mockResolvedValue([
    {
      id: "thread-1",
      title: "Test Thread",
      status: "active",
      scope: "general",
      patient_id: null,
      visibility: "private",
      owner_user_id: "user-1",
      created_trace_id: "t1",
      last_message_at: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ]);

  mockGetThread.mockResolvedValue({
    id: "thread-1",
    title: "Test Thread",
    status: "active",
    scope: "general",
    patient_id: null,
    visibility: "private",
    owner_user_id: "user-1",
    created_trace_id: "t1",
    last_message_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    messages: [],
    participants: [],
  });

  mockPrepareRequest.mockReturnValue({
    ready: true,
    request: { question: "test?", top_k: 5 },
    scope: "general-knowledge",
  });

  mockStreamChat.mockResolvedValue("");
}

/**
 * Enter the bearer token, click Refresh, and wait for the workspace to load.
 * The component requires `apiToken` to be set before it fetches threads.
 */
async function enterTokenAndRefresh(user: ReturnType<typeof userEvent.setup>) {
  const tokenInput = screen.getByPlaceholderText(/bearer token/i);
  await user.type(tokenInput, "dev-doctor");

  const refreshButton = screen.getByText("Refresh");
  await user.click(refreshButton);

  // Wait for workspace to load — the thread title should appear
  await waitFor(() => {
    expect(mockListThreads).toHaveBeenCalled();
  });
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("AssistantShell", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the assistant header and badges", () => {
    render(<AssistantShell />);

    expect(screen.getByText("Ask hospital questions with cited evidence")).toBeInTheDocument();
    expect(screen.getByText("Persisted threads")).toBeInTheDocument();
    expect(screen.getByText("Streaming enabled")).toBeInTheDocument();
  });

  it("renders the conversations sidebar", () => {
    render(<AssistantShell />);

    expect(screen.getByText("Hospital Assistant")).toBeInTheDocument();
    expect(screen.getByText("New conversation")).toBeInTheDocument();
  });

  it("renders patient-linked evidence gate notice", () => {
    render(<AssistantShell />);

    expect(screen.getByText(/patient-linked evidence remains gated/i)).toBeInTheDocument();
  });

  it("shows config-required state before token is entered", () => {
    render(<AssistantShell />);

    expect(
      screen.getByText(/enter a backend bearer token before loading persisted threads/i),
    ).toBeInTheDocument();
  });

  it("loads workspace threads after token is entered and Refresh clicked", async () => {
    render(<AssistantShell />);

    await enterTokenAndRefresh(user);

    await waitFor(() => {
      expect(screen.getAllByText("Test Thread").length).toBeGreaterThan(0);
    });
  });

  it("shows suggested prompts when thread has no messages", async () => {
    render(<AssistantShell />);

    await enterTokenAndRefresh(user);

    await waitFor(() => {
      expect(screen.getByText("Suggested questions")).toBeInTheDocument();
    });
  });

  it("calls streamChat when a question is submitted from an active thread", async () => {
    mockStreamChat.mockImplementation(async (opts: {
      onToken?: (t: string) => void;
      onDone?: (id: string) => void;
    }) => {
      opts.onToken?.("Test answer");
      opts.onDone?.("q-1");
      return "Test answer";
    });

    render(<AssistantShell />);

    await enterTokenAndRefresh(user);

    // Wait for the input to be available
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask general knowledge/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/ask general knowledge/i);
    await user.type(input, "What is the sepsis protocol?");

    const submitButton = screen.getByLabelText("Submit question");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockStreamChat).toHaveBeenCalled();
    });

    const callArgs = mockStreamChat.mock.calls[0][0];
    expect(callArgs.question).toBe("What is the sepsis protocol?");
  });

  it("shows Stop button while streaming and reverts after done", async () => {
    let resolveStream: ((value: string) => void) | undefined;
    mockStreamChat.mockImplementation(
      () =>
        new Promise<string>((resolve) => {
          resolveStream = resolve;
        }),
    );

    render(<AssistantShell />);

    await enterTokenAndRefresh(user);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask general knowledge/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/ask general knowledge/i);
    await user.type(input, "test question");

    const submitButton = screen.getByLabelText("Submit question");
    await user.click(submitButton);

    // Stop button should appear
    await waitFor(() => {
      expect(screen.getByLabelText("Stop generating")).toBeInTheDocument();
    });

    // Resolve the stream
    await act(async () => {
      resolveStream?.("done");
    });

    // Stop button should disappear, Submit button should return
    await waitFor(() => {
      expect(screen.getByLabelText("Submit question")).toBeInTheDocument();
    });
  });
});
