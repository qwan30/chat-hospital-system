# ADR-009: AI Assistant owns RAG, OCR, citations, and threads

## Metadata
- **ID:** ADR-009
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-06-07
- **Last Updated:** 2026-06-07

## Context
We need to define ownership boundaries for AI-centric features (such as user chat histories, vector embeddings, source page coordinates, raw OCR texts, and evaluation metrics) that are not part of the standard transactional clinical domain.

## Decision
The AI Assistant owns all AI-related assets. It stores chat threads, vector embeddings (`document_chunks` table), raw OCR extracted files, safety disclaimers, and user feedback metrics locally in the chatbot's PostgreSQL datastore.

## Consequences
- **Pros:**
  - Avoids polluting the HMS database with high-dimensional vector types (pgvector) and large unstructured text chunks.
  - Allows independent scaling and development of the AI RAG engine.
- **Cons:**
  - The AI Assistant must maintain a mapping between its local vector chunks and the corresponding HMS patient/document record IDs to preserve citation integrity.
