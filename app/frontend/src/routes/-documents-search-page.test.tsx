/** @vitest-environment jsdom */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const searchDocuments = vi.hoisted(() => vi.fn());

vi.mock("@/components/shell/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/lib/api/documents", () => ({ searchDocuments }));

import { DocumentSearchPage } from "./_app.documents.search";

function renderDocumentSearch(searchParams: { q?: string; patientId?: string }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const view = render(
    <QueryClientProvider client={queryClient}>
      <DocumentSearchPage searchParams={searchParams} />
    </QueryClientProvider>,
  );

  return { ...view, queryClient };
}

describe("DocumentSearchPage URL search behavior", () => {
  beforeEach(() => {
    searchDocuments.mockResolvedValue({ items: [] });
  });

  afterEach(() => {
    cleanup();
    searchDocuments.mockReset();
  });

  it("does not submit a q-only legacy URL", async () => {
    renderDocumentSearch({ q: "apixaban" });

    await screen.findByText(/Enter a Patient UUID/i);
    expect(searchDocuments).not.toHaveBeenCalled();
  });

  it("submits exactly the new URL patient scope after navigation", async () => {
    const { rerender, queryClient } = renderDocumentSearch({
      q: "old query",
      patientId: "old-patient",
    });

    await waitFor(() => {
      expect(searchDocuments).toHaveBeenCalledTimes(1);
    });
    searchDocuments.mockClear();

    rerender(
      <QueryClientProvider client={queryClient}>
        <DocumentSearchPage searchParams={{ q: "new query", patientId: "new-patient" }} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(searchDocuments).toHaveBeenCalledTimes(1);
      expect(searchDocuments.mock.calls[0]?.[0]).toEqual({
        patient_id: "new-patient",
        query: "new query",
        top_k: 5,
      });
    });
  });
});
