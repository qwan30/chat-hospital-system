from __future__ import annotations

from typing import Any, Optional


class RAGSpikeAdapter:
    """
    Spike implementation for P2 RAG Hardening.
    Demonstrates isolated, permission-filtered retrieval to prevent patient data leakage.
    """

    def __init__(self, db_session: Any = None):
        self.db_session = db_session

    def retrieve_context(self, query: str, user_role: str, patient_id: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Retrieves context chunks.
        Strictly enforces that if a user is querying about a patient,
        ONLY chunks explicitly tagged with that patient_id are returned.
        """
        # Spike implementation: synthetic hardcoded chunks showing permission enforcement
        synthetic_chunks = [
            {"id": "doc_1", "text": "Patient P-123 is allergic to penicillin.", "patient_id": "P-123"},
            {"id": "doc_2", "text": "Patient P-456 has a history of hypertension.", "patient_id": "P-456"},
            {"id": "doc_3", "text": "General hospital protocol for hypertension.", "patient_id": None},
        ]

        results = []
        for chunk in synthetic_chunks:
            # General info is accessible
            if chunk["patient_id"] is None:
                results.append(chunk)
                continue

            # Patient-specific info requires patient_id match
            if chunk["patient_id"] == patient_id:
                results.append(chunk)

        return results
