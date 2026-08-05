from __future__ import annotations
import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import get_settings
from hospital_ai.db.models import ClinicalAlert, Document, DocumentChunk
from hospital_ai.db.clinical_graph import GraphEntity, GraphRelationAssertion
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.llm.manager import get_llm_manager

logger = logging.getLogger(__name__)


async def run_cdss_analysis(session: AsyncSession, document_id: uuid.UUID) -> None:
    """Run CDSS analysis on a newly indexed document."""
    # 1. Get the document
    document = await session.get(Document, document_id)
    if not document:
        logger.warning("CDSS: Document %s not found.", document_id)
        return

    # 2. Get the text content from chunks
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
    chunks = result.scalars().all()
    text_content = "\n".join(chunk.content for chunk in chunks)

    # 3. Fetch patient's existing GraphContext summary
    entity_result = await session.execute(
        select(GraphEntity).where(GraphEntity.patient_id == document.patient_id)
    )
    all_entities = entity_result.scalars().all()
    all_entities_map = {e.id: e.normalized_label for e in all_entities}
    entity_ids = list(all_entities_map.keys())

    if entity_ids:
        relation_result = await session.execute(
            select(GraphRelationAssertion).where(GraphRelationAssertion.patient_id == document.patient_id)
        )
        all_relations = relation_result.scalars().all()
    else:
        all_relations = []

    context_lines = []
    for e in all_entities:
        context_lines.append(f"- Entity: {e.normalized_label} ({e.entity_type})")
    for r in all_relations:
        source_name = all_entities_map.get(r.subject_entity_id)
        target_name = all_entities_map.get(r.object_entity_id)
        if source_name and target_name:
            context_lines.append(f"- Relation: {source_name} {r.relation_type} {target_name}")

    patient_context_str = "\n".join(context_lines) if context_lines else "No existing context available."

    # 4. Feed to LLM
    prompt = f"""
    You are an advanced Clinical Decision Support System (CDSS).
    Analyze the following new medical document against the patient's existing
    clinical context for any drug interactions, contraindications, or severe risks.

    Patient's existing context (Graph RAG Summary):
    {patient_context_str}

    New Document:
    {text_content}

    Output a JSON object with a list of "alerts", each having "severity"
    (low, medium, high), "title", and "description".
    If no risks are found, output an empty list: {{"alerts": []}}.
    Return ONLY JSON. No markdown formatting.
    """

    llm_manager = get_llm_manager(get_settings())
    llm = llm_manager.get()

    messages = [
        LLMMessage(
            role="system",
            content="You are a medical AI assistant. Always output raw JSON without markdown tags.",
        ),
        LLMMessage(role="user", content=prompt),
    ]

    try:
        response = await llm.generate(messages, temperature=0.0)

        # Parse JSON
        resp_text = response.text.strip()
        if resp_text.startswith("```json"):
            resp_text = resp_text[7:-3].strip()
        elif resp_text.startswith("```"):
            resp_text = resp_text[3:-3].strip()

        data = json.loads(resp_text)
        alerts_data = data.get("alerts", [])

        # 5. Save alerts
        for alert_info in alerts_data:
            # ClinicalAlert.severity is constrained to low/medium/high by
            # ck_clinical_alerts_severity. An unrecognised value means the model
            # returned something we cannot interpret -- including escalations
            # like "critical" or "severe", which the prompt does not ask for but
            # models emit anyway. Fall back to "high" rather than "low": an
            # uninterpretable clinical severity must not be silently downgraded
            # to the value a clinician triages last.
            raw_severity = str(alert_info.get("severity", "")).strip().lower()
            if raw_severity in ("low", "medium", "high"):
                severity = raw_severity
            else:
                severity = "high"
                logger.warning(
                    "CDSS returned unrecognised severity %r for document %s; escalating to 'high'",
                    raw_severity,
                    document_id,
                )

            alert = ClinicalAlert(
                patient_id=document.patient_id,
                source_document_id=document_id,
                severity=severity,
                title=alert_info.get("title", "Clinical Alert"),
                description=alert_info.get("description", ""),
            )
            session.add(alert)

        if alerts_data:
            await session.commit()

    except Exception:
        logger.exception("CDSS analysis failed for %s", document_id)
        raise
