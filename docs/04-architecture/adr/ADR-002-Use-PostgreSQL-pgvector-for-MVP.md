# ADR-002: Use PostgreSQL + pgvector for MVP

## Metadata
- **ID:** ADR-002
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-04-27
- **Last Updated:** 2026-06-07

## Context
The AI assistant must perform semantic document searches over chunks of scanned patient documents and medical history. This requires a database that supports both structured transactional relational queries (such as patient profile mappings and RBAC/ABAC audits) and vector similarity searches (such as cosine distance on text embeddings).

## Decision
We chose PostgreSQL with the `pgvector` extension as the primary relational and vector datastore for the MVP.

## Alternatives Considered
- **Dedicated Vector DB (Pinecone/Milvus/Qdrant):** Highly optimized for large vector scales (millions of records), but introduces operational overhead, network latency, extra licensing costs, and complicates relational join queries (e.g., joining permissions, audits, and vector chunks).
- **SQLite + sqlite-vss:** Very lightweight, but lacks the concurrency, robustness, security controls, and enterprise-readiness needed for hospital systems.

## Consequences
- **Pros:**
  - Keeps all patient profiles, document chunks, vectors, audit logs, and metrics in a single database instance.
  - Allows single SQL queries to join transactional data and vector search results (e.g., filtering chunks by user-authorized patient IDs before similarity matching).
  - Familiar ecosystem for deployment and maintenance.
- **Cons:**
  - May have lower query performance than dedicated vector databases at extreme scales (over 10 million vector records). This is mitigated by indexing strategies (IVFFlat/HNSW) in pgvector.
