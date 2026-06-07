# ADR-001: Use FastAPI

## Metadata
- **ID:** ADR-001
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-04-27
- **Last Updated:** 2026-06-07

## Context
We need a high-performance web framework for the Python backend of the AI-Powered Hospital Knowledge Assistant. The backend will orchestrate OCR workers, embedding models, vector retrievals, and local LLM chat queries. It must support high concurrency, async event handling, automatic OpenAPI/Swagger documentation, and clean validation schemas.

## Decision
We chose FastAPI as the primary backend web framework.

## Alternatives Considered
- **Flask:** Light and simple, but lacks native asynchronous support and built-in type-hint-based request/response validation (requires extra libraries like Pydantic + Marshmallow).
- **Django:** Extremely robust and feature-rich, but excessively heavy for an API-only service that does not need Django's built-in templates, forms, or legacy ORM features.

## Consequences
- **Pros:**
  - Extremely fast performance comparable to NodeJS and Go (using Uvicorn/Starlette).
  - Native asynchronous support (`async/await`) for concurrency.
  - Automatic OpenAPI / Swagger UI generation, saving development documentation time.
  - Integrated with Pydantic for strict runtime type-checking and request validation.
- **Cons:**
  - Requires developers to understand async programming constructs in Python.
  - Requires separate database integration libraries (e.g., SQLAlchemy or Tortoise ORM) rather than a built-in ORM.
