# ADR-005: Add Neo4j in Phase 2

## Metadata
- **ID:** ADR-005
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-04-27
- **Last Updated:** 2026-06-07

## Context
Standard semantic search retrieve separate text chunks that may miss complex relationships (e.g., patient → diagnoses → medications → prescribing doctors). Connecting these clinical entities into a knowledge graph enables Graph RAG, improving the accuracy of complex relationship-based queries. However, running a graph database like Neo4j alongside PostgreSQL, Ollama, and OCR exceeds the 16GB RAM limit for the initial MVP.

## Decision
We decided to defer the integration of Neo4j to Phase 2. For the MVP, we will model simple clinical entity relationships using PostgreSQL relational tables (SQL Graph MVP).

## Alternatives Considered
- **Running Neo4j in MVP:** Excluded because the RAM footprint (Neo4j JVM typically needs at least 2-4GB RAM) would violate the 16GB total system memory limit when running alongside local Ollama (4GB) and OCR processes.
- **Using pg_routing or ltree:** Relational tools that could support graphs inside Postgres. While useful, they lack the native graph visualization and cypher query optimizations of Neo4j needed for long-term scalability.

## Consequences
- **Pros:**
  - Guarantees the MVP fits on a 16GB RAM local instance.
  - Simplifies the initial software stack deployment and reduces operational complexity.
- **Cons:**
  - Complex relationship queries will be slower and harder to write in the MVP, as they require recursive PostgreSQL CTE joins.
  - Requires a data migration and syncing pipeline to load entities from PostgreSQL to Neo4j in Phase 2.
