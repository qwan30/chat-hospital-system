export interface StreamScope {
  patientId?: string;
  threadId?: string;
}

export function hasStreamScopeChanged(active: StreamScope, current: StreamScope): boolean {
  return active.patientId !== current.patientId || active.threadId !== current.threadId;
}

export function isCurrentStreamRequest(
  active: AbortController | null,
  request: AbortController | null,
): boolean {
  return request !== null && active === request;
}
