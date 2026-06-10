import { apiFetch, type ApiClientOptions, type GlobalSearchResult } from "@/lib/api-client";

export function globalSearch(opts: ApiClientOptions, query: string): Promise<GlobalSearchResult> {
  const params = new URLSearchParams({ q: query }).toString();
  return apiFetch<GlobalSearchResult>("/search/global?" + params, { ...opts, method: "GET" });
}
