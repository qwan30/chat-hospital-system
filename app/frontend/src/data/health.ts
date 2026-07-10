export interface HealthMetric {
  name: string;
  status: "ok" | "degraded" | "down";
  value: string;
  detail: string;
}

export const systemHealth: HealthMetric[] = [
  {
    name: "HMS API",
    status: "degraded",
    value: "p95 1.8s",
    detail: "Last sync 18 min ago · target 15 min",
  },
  {
    name: "Vector index",
    status: "ok",
    value: "12.4M chunks",
    detail: "Last rebuild 03:14 UTC · 4m 12s",
  },
  {
    name: "LLM runtime (Ollama)",
    status: "ok",
    value: "p95 1.4s",
    detail: "Qwen2.5-7B · 14.2GB mem · 2 GPUs",
  },
  { name: "Embeddings", status: "ok", value: "p95 84ms", detail: "bge-large-en · queue depth 0" },
  {
    name: "Audit ledger",
    status: "ok",
    value: "0 gaps",
    detail: "Hash chain verified at 16:00 UTC",
  },
];

export const vectorIndexHealth = {
  collections: [
    { name: "documents-2026", chunks: 8_420_112, lastWrite: "2026-06-12T15:58:00Z", drift: 0.02 },
    { name: "documents-2025", chunks: 3_180_044, lastWrite: "2026-01-04T00:14:00Z", drift: 0.0 },
    { name: "guidelines", chunks: 812_400, lastWrite: "2026-05-30T11:00:00Z", drift: 0.01 },
  ],
  totalChunks: 12_412_556,
  embeddingModel: "bge-large-en-v1.5",
  dimension: 1024,
  status: "ok" as const,
};

export const llmHealth = {
  model: "Qwen2.5-7B-Instruct (Q5_K_M)",
  runtime: "Ollama 0.4.2",
  gpus: [
    { id: "gpu-0", mem: "14.2 / 24 GB", util: 62 },
    { id: "gpu-1", mem: "13.8 / 24 GB", util: 58 },
  ],
  p50Ms: 820,
  p95Ms: 1420,
  p99Ms: 2100,
  qps: 4.2,
  status: "ok" as const,
};
