from __future__ import annotations
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

# RQ jobs mapping to the 6 stages


def stage_preflight(document_id: uuid.UUID, run_id: uuid.UUID, config_version: int) -> dict[str, Any]:
    logger.info(f"Running preflight for doc {document_id}, run {run_id}")
    return {"status": "completed"}


def stage_pages_extraction(document_id: uuid.UUID, run_id: uuid.UUID, config_version: int) -> dict[str, Any]:
    logger.info(f"Running pages_extraction for doc {document_id}, run {run_id}")
    return {"status": "completed"}


def stage_ocr_vision(document_id: uuid.UUID, run_id: uuid.UUID, config_version: int) -> dict[str, Any]:
    logger.info(f"Running ocr_vision for doc {document_id}, run {run_id}")
    return {"status": "completed"}


def stage_fact_extraction(document_id: uuid.UUID, run_id: uuid.UUID, config_version: int) -> dict[str, Any]:
    logger.info(f"Running fact_extraction for doc {document_id}, run {run_id}")
    return {"status": "completed"}


def stage_index(document_id: uuid.UUID, run_id: uuid.UUID, config_version: int) -> dict[str, Any]:
    logger.info(f"Running index for doc {document_id}, run {run_id}")
    return {"status": "completed"}


def stage_cdss(document_id: uuid.UUID, run_id: uuid.UUID, config_version: int) -> dict[str, Any]:
    logger.info(f"Running cdss for doc {document_id}, run {run_id}")
    return {"status": "completed"}


def build_fhir_draft(document_id: uuid.UUID, run_id: uuid.UUID, config_version: int) -> dict[str, Any]:
    logger.info(f"Building FHIR draft for doc {document_id}")
    # Security finding: Update policy to EXCLUDE unreviewed high-risk items from FHIR draft.
    # Stub implementation reflecting the policy:
    # facts = get_facts(document_id)
    # safe_facts = [f for f in facts if not (f.risk_class == "high" and f.review_status == "unreviewed")]
    # draft = generate_draft(safe_facts)
    return {"status": "completed"}
