"""
Domain Exceptions for Hospital AI Knowledge Assistant.

These exceptions represent pure business-rule violations — they carry
NO framework dependencies (no HTTP status codes, no FastAPI imports).
The API layer maps them to HTTP responses via exception handlers.

Architecture principle (Clean Architecture / Dependency Rule):
    Domain exceptions live in core/ so business logic can raise them
    without importing the web framework. The presentation layer
    (api/) catches them and decides how to present them to clients.
"""
from __future__ import annotations

from typing import Any, Optional


class AppError(Exception):
    """Base class for all application-level domain exceptions.

    Every domain exception inherits from this so the API exception
    handler can catch them uniformly with a single ``@app.exception_handler``.

    Attributes:
        code: Machine-readable error code (e.g. "MEDICAL_DATA_ACCESS_DENIED").
        message: Human-readable description for logging and client display.
        metadata: Optional dict of contextual data (e.g. patient_id, role).
    """

    def __init__(self, code: str, message: str, metadata: Optional[dict[str, Any]] = None) -> None:
        self.code = code
        self.message = message
        self.metadata = metadata or {}
        super().__init__(message)


# ── Security & Access Control ────────────────────────────────────────


class MedicalDataAccessException(AppError):
    """Raised when a user attempts to access PHI outside their scope.

    This is the critical security boundary — it fires when the permission
    filter in the vector search detects that a retrieved document chunk
    belongs to a patient the user is NOT authorized to view.

    Example triggers:
        - Doctor A tries to query patient records of Doctor B's patient.
        - Nurse tries to access restricted admin-only policy documents.
        - Citation validator finds a chunk with mismatched role permissions.
    """

    def __init__(self, message: str = "Access to medical data denied", **metadata: Any) -> None:
        super().__init__("MEDICAL_DATA_ACCESS_DENIED", message, metadata)


class PermissionDeniedException(AppError):
    """Raised when a user's role lacks the required permission for an action.

    Distinct from MedicalDataAccessException — this covers general RBAC
    violations (e.g. pharmacist trying to access audit logs), while
    MedicalDataAccessException is specifically for PHI boundary violations.
    """

    def __init__(self, message: str = "Permission denied", **metadata: Any) -> None:
        super().__init__("PERMISSION_DENIED", message, metadata)


class AuthenticationException(AppError):
    """Raised when JWT validation fails or credentials are invalid.

    Covers: expired tokens, invalid signatures, missing credentials,
    and account-locked scenarios.
    """

    def __init__(self, message: str = "Authentication failed", **metadata: Any) -> None:
        super().__init__("AUTHENTICATION_FAILED", message, metadata)


# ── AI / RAG Quality ─────────────────────────────────────────────────


class CitationHallucinationException(AppError):
    """Raised when the LLM generates a citation that cannot be verified.

    The Citation Validator checks every source reference in the LLM
    response against the actual document chunk database. If a citation
    points to a non-existent chunk, or the chunk content doesn't match
    the cited text, this exception fires to BLOCK the response from
    being streamed to the user.

    This is a safety-critical check — hallucinated citations in a
    clinical context could lead to incorrect medical decisions.
    """

    def __init__(self, message: str = "LLM generated unverifiable citation", **metadata: Any) -> None:
        super().__init__("CITATION_HALLUCINATION", message, metadata)


class RAGRetrievalException(AppError):
    """Raised when the RAG pipeline fails to retrieve relevant context.

    Covers: empty vector search results, embedding generation failures,
    and graph RAG traversal errors.
    """

    def __init__(self, message: str = "RAG retrieval failed", **metadata: Any) -> None:
        super().__init__("RAG_RETRIEVAL_FAILED", message, metadata)


# ── Document Processing ──────────────────────────────────────────────


class DocumentProcessingException(AppError):
    """Raised when document ingestion, OCR, or chunking fails.

    Covers: PDF parsing errors, OCR failures (PaddleOCR), unsupported
    file formats, chunking pipeline errors, and embedding generation
    failures during document processing.
    """

    def __init__(self, message: str = "Document processing failed", **metadata: Any) -> None:
        super().__init__("DOCUMENT_PROCESSING_FAILED", message, metadata)


class UnsupportedDocumentFormatException(DocumentProcessingException):
    """Raised when an uploaded file format is not supported for processing."""

    def __init__(self, filename: str = "", **metadata: Any) -> None:
        super().__init__(
            f"Unsupported document format: {filename or 'unknown'}",
            filename=filename,
            **metadata,
        )


# ── External Integration ─────────────────────────────────────────────


class HMSIntegrationException(AppError):
    """Raised when the external Hospital Management System API fails.

    Covers: connection timeouts, HTTP error responses, authentication
    failures to HMS, and data sync conflicts.
    """

    def __init__(self, message: str = "HMS integration failed", **metadata: Any) -> None:
        super().__init__("HMS_INTEGRATION_FAILED", message, metadata)


class LLMProviderException(AppError):
    """Raised when the LLM provider (Ollama, OpenAI) returns an error.

    Covers: connection failures, timeout errors, rate limiting, and
    malformed responses from the LLM API.
    """

    def __init__(self, message: str = "LLM provider error", **metadata: Any) -> None:
        super().__init__("LLM_PROVIDER_ERROR", message, metadata)


class EmbeddingProviderException(AppError):
    """Raised when the embedding provider fails to generate embeddings.

    Covers: model loading failures, API errors, and dimension mismatches.
    """

    def __init__(self, message: str = "Embedding provider error", **metadata: Any) -> None:
        super().__init__("EMBEDDING_PROVIDER_ERROR", message, metadata)


# ── Data Integrity ───────────────────────────────────────────────────


class EntityNotFoundException(AppError):
    """Raised when a requested database entity does not exist.

    Used generically for any entity type (patient, document, thread, etc.).
    The metadata dict should include entity_type and entity_id.
    """

    def __init__(self, entity_type: str = "Entity", entity_id: str = "", **metadata: Any) -> None:
        super().__init__(
            "ENTITY_NOT_FOUND",
            f"{entity_type} not found: {entity_id}",
            {"entity_type": entity_type, "entity_id": entity_id, **metadata},
        )


class ValidationException(AppError):
    """Raised when input data fails business rule validation.

    Distinct from Pydantic validation errors (which are caught at the
    API layer) — this is for domain-level validation like "cannot
    prescribe drug X with active allergy Y."
    """

    def __init__(self, message: str = "Validation failed", **metadata: Any) -> None:
        super().__init__("VALIDATION_FAILED", message, metadata)
