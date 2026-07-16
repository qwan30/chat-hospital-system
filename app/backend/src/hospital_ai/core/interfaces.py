"""
Abstract Interface Protocols for Hospital AI.
Định nghĩa các giao thức giao diện trừu tượng cho Trợ lý Tri thức Bệnh viện AI.

Defines framework-agnostic contracts that core business logic depends on.
Concrete implementations live in services/ and infrastructure layers.
Định nghĩa các hợp đồng (contracts) độc lập với framework mà logic nghiệp vụ cốt lõi phụ thuộc vào.
Các lớp triển khai cụ thể (concrete implementations) nằm trong các tầng services/ và infrastructure.

This enforces the Clean Architecture Dependency Rule:
    core/ depends ONLY on these abstract interfaces (inward-facing).
    services/ implements them (outward-facing, depends on core/).
    api/ wires concrete implementations at startup.

Usage pattern:
    def some_service(llm: ILLMProvider, embedder: IEmbeddingProvider) -> str:
        # Works with ANY implementation — Ollama, OpenAI, stub for testing
        ...
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

# ── LLM Provider ─────────────────────────────────────────────────────


class ILLMProvider(ABC):
    """Abstract interface for language model providers.
    Giao diện trừu tượng cho các nhà cung cấp mô hình ngôn ngữ lớn (LLM).

    Decouples RAG pipeline from specific LLM backends (Ollama, OpenAI, etc.).
    Core services depend on this interface — never on concrete implementations.
    Giúp tách biệt (decouple) RAG pipeline khỏi các backend LLM cụ thể như Ollama hay OpenAI.
    """

    @abstractmethod
    async def generate(self, prompt: str, context: str, **kwargs: Any) -> str:
        """Generate a response given a prompt and retrieved context.

        Args:
            prompt: The system/user prompt template.
            context: Retrieved and filtered context from vector search.
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.).

        Returns:
            The generated text response.

        Raises:
            LLMProviderException: On provider errors (timeout, rate limit, etc.).
        """
        ...

    @abstractmethod
    async def stream(self, prompt: str, context: str, **kwargs: Any) -> Any:
        """Stream a response as an async generator of text chunks.

        Args:
            prompt: The system/user prompt template.
            context: Retrieved and filtered context from vector search.
            **kwargs: Provider-specific parameters.

        Yields:
            Text chunks as they are generated.

        Raises:
            LLMProviderException: On provider errors.
        """
        ...


# ── Embedding Provider ───────────────────────────────────────────────


class IEmbeddingProvider(ABC):
    """Abstract interface for text embedding providers.

    Supports multiple backends: deterministic (testing), Ollama, OpenAI, Cohere.
    """

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of text inputs.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each as list[float]), same order as texts.

        Raises:
            EmbeddingProviderException: On provider errors.
        """
        ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Generate an embedding for a single query text.

        Args:
            text: The query string to embed.

        Returns:
            A single embedding vector as list[float].

        Raises:
            EmbeddingProviderException: On provider errors.
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension (e.g. 768, 1536)."""
        ...


# ── HMS Connector ────────────────────────────────────────────────────


class IHMSConnector(ABC):
    """Abstract interface for Hospital Management System integration.

    Decouples RAG services from the specific HMS API implementation.
    """

    @abstractmethod
    async def get_patient(self, patient_id: str) -> dict[str, Any]:
        """Fetch patient demographic and medical record summary.

        Args:
            patient_id: The patient identifier.

        Returns:
            Patient data dict with keys: id, name, dob, allergies, medications, etc.

        Raises:
            HMSIntegrationException: On connection or API errors.
            EntityNotFoundException: If patient not found in HMS.
        """
        ...

    @abstractmethod
    async def get_appointments(self, patient_id: str) -> list[dict[str, Any]]:
        """Fetch upcoming and recent appointments for a patient.

        Args:
            patient_id: The patient identifier.

        Returns:
            List of appointment dicts with date, type, provider, status.

        Raises:
            HMSIntegrationException: On connection or API errors.
        """
        ...

    @abstractmethod
    async def sync_patient_data(self, patient_id: str) -> bool:
        """Trigger HMS data sync for a patient (pull latest records).

        Args:
            patient_id: The patient identifier.

        Returns:
            True if sync succeeded, False otherwise.

        Raises:
            HMSIntegrationException: On critical sync failures.
        """
        ...


# ── User Context ─────────────────────────────────────────────────────


@runtime_checkable
class IUserContext(Protocol):
    """Protocol for authenticated user context passed to core services.

    This is a Protocol (structural subtyping) rather than ABC —
    any object with these attributes satisfies the interface.
    This lets us pass FastAPI request.state or test doubles
    without any framework coupling in core/.

    Attributes:
        user_id: Unique user identifier (UUID string).
        role: RBAC role (doctor, nurse, pharmacist, admin).
        permissions: Set of permission strings for ABAC checks.
    """

    user_id: str
    role: str
    permissions: set[str]


# ── Database Session ─────────────────────────────────────────────────


class IDatabaseSession(ABC):
    """Abstract interface for database access in core services.

    Decouples core logic from SQLAlchemy async sessions.
    Enables in-memory repository doubles for fast unit tests.
    """

    @abstractmethod
    async def execute(self, query: Any) -> Any:
        """Execute a database query and return results."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...


# ── Citation Validator ───────────────────────────────────────────────


class ICitationValidator(ABC):
    """Abstract interface for citation verification.

    The concrete implementation checks every LLM-generated citation
    against the actual document chunk database to detect hallucinations.
    """

    @abstractmethod
    async def validate(self, citations: list[dict[str, Any]], context_chunks: list[dict[str, Any]]) -> bool:
        """Validate that all citations reference real, accessible chunks.

        Args:
            citations: List of citation dicts from LLM response.
            context_chunks: The actual chunks used as RAG context.

        Returns:
            True if all citations are valid and match actual chunks.

        Raises:
            CitationHallucinationException: If any citation is hallucinated.
        """
        ...


# ── Audit Logger ─────────────────────────────────────────────────────


class IAuditLogger(ABC):
    """Abstract interface for audit event recording.

    All clinical data access, permission denials, and config changes
    must be logged through this interface for compliance.
    """

    @abstractmethod
    async def log(self, user_id: str, action: str, details: dict[str, Any]) -> None:
        """Record an audit event.

        Args:
            user_id: The user who performed the action.
            action: Machine-readable action name (e.g. "query_patient", "upload_document").
            details: Contextual data (patient_id, document_id, result, etc.).
        """
        ...
