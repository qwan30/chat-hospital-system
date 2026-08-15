export function mutationHeaders(options: {
  idempotencyKey: string;
  lockVersion?: number;
}): Record<string, string> {
  return {
    "Idempotency-Key": options.idempotencyKey,
    ...(options.lockVersion === undefined ? {} : { "If-Match": String(options.lockVersion) }),
  };
}

export function newIdempotencyKey(scope: string): string {
  return `${scope}:${crypto.randomUUID()}`;
}
