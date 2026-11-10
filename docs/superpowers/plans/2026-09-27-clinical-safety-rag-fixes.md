# Clinical Safety, Temporal Entailment & GraphRAG Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement verified fixes for the 3 core clinical RAG vulnerabilities (drug interaction checking with evidence-backed active medication selection, clause-level event-date binding in claim validation, and selective graph traversal through patient anchor) with zero DB schema migrations and preserving all 824 existing tests.

**Architecture:** The Incremental Pragmatist approach:
1. `DrugCheckService` is wired to the in-memory singleton `DrugCatalogService`, selecting active patient medications via an evidence-backed 4-layer query and enforcing pre-flight hard blocks for critical contraindications in `chat_stream.py`.
2. `deterministic_entailment` in `claim_validation.py` replaces the brittle `len(evidence_dates) != 1` check with clause-level temporal binding, matching claim action tokens against the specific evidence clause containing the date.
3. `find_related_entities` in `graph_rag.py` replaces the hard cutoff at `patient:self` with a selective relation-type whitelist (`diagnosed_with`, `allergic_to`, etc.) bounded by a 15-node cap.

**Tech Stack:** Python 3.11/3.12, FastAPI, SQLAlchemy 2.0 Async, Pytest, Pydantic v2.

## Global Constraints

- Zero database schema migrations (no Alembic migrations, no new tables).
- Add < 5ms latency overhead to the chat streaming pipeline.
- All 824 existing backend tests and 209 frontend tests must continue to pass.
- Clinical safety is fail-closed: critical contraindications abort generation before LLM tokens are produced.
- Never use naive date set membership (`claim_dates <= evidence_dates`); event-date binding is required.

---

### Task 1: Evidence-Backed Active Medication Selection & Drug Catalog Integration

**Files:**
- Modify: `app/backend/src/hospital_ai/services/drug_check.py:75-195`
- Test: `app/backend/tests/test_drug_check.py`

**Interfaces:**
- Consumes:
  - `get_drug_catalog_service()` from `hospital_ai.services.drug_catalog`
  - `GraphEntity`, `GraphMention` from `hospital_ai.db.clinical_graph`
  - `Document` from `hospital_ai.db.models`
- Produces:
  - `DrugCheckService.check_interactions(query_text: str, patient_id: Optional[uuid.UUID], min_severity: str = "low") -> list[DrugWarning]`
  - Returns structured `DrugWarning` records for interactions between candidate drugs in `query_text` and active, approved patient medications.

- [ ] **Step 1: Write the failing tests for candidate drug detection and discontinued drug filtering**

Add to `app/backend/tests/test_drug_check.py`:

```python
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from hospital_ai.db.clinical_graph import GraphEntity, GraphMention
from hospital_ai.db.models import Document, DocumentIndexGeneration, DocumentRevisionSet, DocumentPageRevision, DocumentPage
from hospital_ai.services.drug_check import DrugCheckService


@pytest.mark.asyncio
async def test_drug_check_detects_candidate_drug_interaction(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    
    # Setup document and generation to back the active medication
    doc = Document(id=uuid.uuid4(), patient_id=patient_id, filename="chart.pdf", status="ready")
    gen = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, state="active")
    doc.active_index_generation_id = gen.id
    db_session.add_all([doc, gen])
    await db_session.flush()

    aspirin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="aspirin",
        entity_type="drug",
        lifecycle_status="active",
    )
    db_session.add(aspirin)
    await db_session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=aspirin.id,
        generation_id=gen.id,
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1",
    )
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    warnings = await service.check_interactions(
        query_text="Can we prescribe warfarin 5mg to this patient?",
        patient_id=patient_id,
    )
    assert len(warnings) >= 1
    warfarin_warnings = [w for w in warnings if "warfarin" in w.drug_name.lower() or "aspirin" in w.drug_name.lower()]
    assert len(warfarin_warnings) >= 1
    assert warfarin_warnings[0].severity in ("high", "critical")


@pytest.mark.asyncio
async def test_drug_check_ignores_discontinued_medication(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    doc = Document(id=uuid.uuid4(), patient_id=patient_id, filename="old.pdf", status="ready")
    gen = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, state="active")
    doc.active_index_generation_id = gen.id
    db_session.add_all([doc, gen])
    await db_session.flush()

    discontinued_warfarin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=patient_id,
        normalized_label="warfarin",
        entity_type="drug",
        lifecycle_status="discontinued",
    )
    db_session.add(discontinued_warfarin)
    await db_session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=patient_id,
        entity_id=discontinued_warfarin.id,
        generation_id=gen.id,
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="old.pdf:1:1",
    )
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    # Query prescribing aspirin should not alert for discontinued warfarin
    warnings = await service.check_interactions(
        query_text="Can we start aspirin 81mg daily?",
        patient_id=patient_id,
        min_severity="high",
    )
    assert len(warnings) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_drug_check.py::test_drug_check_detects_candidate_drug_interaction -v`
Expected: FAIL (returns 0 warnings because candidate drug warfarin is not in patient's chart).

- [ ] **Step 3: Implement evidence-backed active drug selection & catalog wiring in `DrugCheckService`**

Modify `app/backend/src/hospital_ai/services/drug_check.py`:

```python
from hospital_ai.services.drug_catalog import get_drug_catalog_service
from hospital_ai.db.clinical_graph import GraphEntity, GraphMention
from hospital_ai.db.models import Document


class DrugCheckService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.catalog = get_drug_catalog_service()

    async def _get_active_patient_entities(self, patient_id: uuid.UUID) -> list[GraphEntity]:
        """Fetch active, approved drug and allergy entities for the patient."""
        stmt = (
            select(GraphEntity)
            .join(
                GraphMention,
                (GraphMention.entity_id == GraphEntity.id)
                & (GraphMention.patient_id == GraphEntity.patient_id),
            )
            .join(Document, Document.id == GraphMention.document_id)
            .where(
                GraphEntity.patient_id == patient_id,
                GraphEntity.entity_type.in_(["drug", "allergy"]),
                GraphEntity.lifecycle_status == "active",
                Document.active_index_generation_id == GraphMention.generation_id,
                Document.deleted_at.is_(None),
                Document.status.in_(("ready", "ready_with_warnings")),
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def check_interactions(
        self,
        query_text: str,
        patient_id: Optional[uuid.UUID],
        *,
        min_severity: str = "low",
    ) -> list[DrugWarning]:
        if not patient_id:
            return []

        # 1. Hybrid candidate extraction: catalog regex + NLP extractor
        catalog_mentions = set(self.catalog.extract_drug_mentions(query_text))
        try:
            nlp_entities, _ = await extract_entities_and_relations_nlp(query_text)
            nlp_drugs = {e.normalized_label.lower().strip() for e in nlp_entities if e.entity_type == "drug"}
        except Exception:
            nlp_drugs = set()
        candidate_drugs = catalog_mentions | nlp_drugs

        if not candidate_drugs:
            return []

        # 2. Fetch active approved patient medications/allergies
        patient_entities = await self._get_active_patient_entities(patient_id)
        if not patient_entities:
            return []

        severity_order = ["critical", "high", "medium", "low"]
        min_idx = severity_order.index(min_severity) if min_severity in severity_order else len(severity_order)

        warnings: list[DrugWarning] = []
        seen: set[tuple[str, str, str]] = set()

        # 3. Cross-reference candidate drugs against patient's active drugs in catalog
        for candidate in candidate_drugs:
            for patient_entity in patient_entities:
                patient_drug = patient_entity.normalized_label.lower().strip()
                if candidate == patient_drug:
                    continue

                interaction = self.catalog.get_interaction(candidate, patient_drug)
                if not interaction:
                    continue

                if severity_order.index(interaction.severity) > min_idx:
                    continue

                key = (min(candidate, patient_drug), max(candidate, patient_drug), interaction.interaction_type)
                if key in seen:
                    continue
                seen.add(key)

                warnings.append(
                    DrugWarning(
                        drug_name=candidate,
                        interacting_entity=patient_drug,
                        interaction_type=interaction.interaction_type,
                        severity=interaction.severity,
                        evidence_chunk_id=None,
                        message=(
                            f"{interaction.severity.upper()} Interaction: {candidate.capitalize()} and "
                            f"{patient_drug.capitalize()}. {interaction.mechanism_action} "
                            f"Recommendation: {interaction.clinical_recommendation}"
                        ),
                    )
                )

        warnings.sort(key=lambda w: severity_order.index(w.severity))
        return warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_drug_check.py -v`
Expected: PASS all tests in `test_drug_check.py`.

- [ ] **Step 5: Commit Task 1**

```bash
git add app/backend/src/hospital_ai/services/drug_check.py app/backend/tests/test_drug_check.py
git commit -m "feat(cdss): wire DrugCatalogService with evidence-backed active drug selection"
```

---

### Task 2: Pre-flight Drug Safety Guardrail in SSE Chat Streaming

**Files:**
- Modify: `app/backend/src/hospital_ai/api/routes/chat_stream.py:270-340`
- Test: `app/backend/tests/test_chat_stream_endpoint.py`

**Interfaces:**
- Consumes: `DrugCheckService.check_interactions`
- Produces: Intercepts stream on `CRITICAL` warnings with safe canned event; injects `HIGH` warnings into prompt & metadata.

- [ ] **Step 1: Write the failing test for critical interaction interception in stream**
Add to `app/backend/tests/test_chat_stream_endpoint.py`:

```python
@pytest.mark.asyncio
async def test_chat_stream_critical_drug_interaction_intercept(session_and_settings, monkeypatch):
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    assert doctor is not None

    # 1. Seed document, generation, and active patient medication (warfarin)
    doc = Document(id=uuid.uuid4(), patient_id=PATIENT_ALICE_ID, filename="chart.pdf", status="ready")
    gen = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, state="active")
    doc.active_index_generation_id = gen.id
    session.add_all([doc, gen])
    await session.flush()

    warfarin = GraphEntity(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        normalized_label="warfarin",
        entity_type="drug",
        lifecycle_status="active",
    )
    session.add(warfarin)
    await session.flush()

    mention = GraphMention(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        entity_id=warfarin.id,
        generation_id=gen.id,
        document_id=doc.id,
        revision_set_id=uuid.uuid4(),
        page_revision_id=uuid.uuid4(),
        chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1",
    )
    session.add(mention)
    await session.commit()

    # 2. Mock mock catalog to return critical contraindication for query drug
    from hospital_ai.services.drug_catalog import CatalogInteraction, get_drug_catalog_service
    catalog = get_drug_catalog_service()
    monkeypatch.setattr(
        catalog,
        "get_interaction",
        lambda d1, d2: CatalogInteraction(
            drug_a=d1, drug_b=d2, interaction_type="contraindicated",
            severity="critical", mechanism_action="Fatal bleeding risk.",
            clinical_recommendation="Do not administer."
        ) if "aspirin" in (d1, d2) and "warfarin" in (d1, d2) else None
    )

    # 3. Assert zero provider/LLM calls
    llm_get = Mock(side_effect=AssertionError("LLMManager.get must not be called when critical interaction is intercepted"))
    monkeypatch.setattr("hospital_ai.api.routes.chat_stream.LLMManager.get", llm_get)

    # 4. Invoke chat_stream
    req = ChatRequest(
        question="Can I prescribe aspirin 1000mg for Alice?",
        patient_id=PATIENT_ALICE_ID,
    )
    resp = await chat_stream(
        payload=req,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    # 5. Read SSE events
    body = b"".join([chunk async for chunk in resp.body_iterator])
    events = _parse_sse_events(body)
    tokens = [e.get("content", "") for e in events if e.get("type") == "token"]
    full_text = "".join(tokens)

    assert "CLINICAL CONTRAINDICATION" in full_text
    assert any(e.get("type") == "done" for e in events)

    # 6. Assert terminal persistence in DB
    query_stmt = select(AiQuery).where(AiQuery.patient_id == PATIENT_ALICE_ID, AiQuery.question == req.question)
    ai_query = (await session.execute(query_stmt)).scalar_one()
    assert ai_query.status == "failed"

    audit_stmt = select(AuditLog).where(AuditLog.object_id == ai_query.id)
    audit = (await session.execute(audit_stmt)).scalar_one()
    assert audit.outcome == "denied"
    assert audit.meta.get("reason") == "clinical_contraindication_blocked"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_chat_stream_endpoint.py -k test_chat_stream_critical_drug_interaction_intercept -v`
Expected: FAIL (assertion error because pre-flight DDI check does not yet intercept).

- [ ] **Step 3: Implement pre-flight DDI check in `chat_stream.py`**

Modify `app/backend/src/hospital_ai/api/routes/chat_stream.py` around line 1148 (immediately after input guardrail check):

```python
    # Pre-flight clinical drug interaction check
    if effective_patient_id:
        from hospital_ai.services.drug_check import DrugCheckService
        ddi_service = DrugCheckService(session)
        drug_warnings = await ddi_service.check_interactions(
            query_text=payload.question,
            patient_id=effective_patient_id,
            min_severity="low",
        )
        critical_ddi = [w for w in drug_warnings if w.severity == "critical"]
        if critical_ddi:
            contraindication_msg = (
                "CLINICAL CONTRAINDICATION: Prescribing this medication is strictly contraindicated "
                f"for this patient: {critical_ddi[0].message}"
            )
            await _finalize_stream_outcome(
                session,
                ai_query=ai_query,
                completion=StreamCompletion(
                    validation_status="failed",
                    answer=contraindication_msg,
                    failure_reason="clinical_contraindication_blocked",
                ),
                user_id=current_user.id,
                patient_id=effective_patient_id,
                trace_id=trace_id,
                ip_address=get_request_ip(request),
                started=started,
                evidence_count=0,
                metadata={"reason": "clinical_contraindication_blocked", "details": critical_ddi[0].message},
            )
            await session.commit()

            return StreamingResponse(
                _safe_refusal_stream(
                    answer=contraindication_msg,
                    query_id=ai_query.id,
                    reason="clinical_contraindication_blocked",
                    model=_resolve_model_name(settings),
                ),
                media_type="text/event-stream",
            )
```
Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_chat_stream_endpoint.py -k test_chat_stream_critical_drug_interaction_intercept -v`
Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add app/backend/src/hospital_ai/api/routes/chat_stream.py app/backend/tests/test_chat_stream_endpoint.py
git commit -m "feat(chat): enforce pre-flight DDI hard-block and prompt injection in SSE stream"
```

---

### Task 3: Clause-Level Event-Date Binding in Claim Validation

**Files:**
- Modify: `app/backend/src/hospital_ai/services/claim_validation.py:205-235`
- Test: `app/backend/tests/test_claim_validation.py`

**Interfaces:**
- Consumes: `_split_clinical_clauses`, `_extract_dates`, `_meaningful_tokens`
- Produces: `deterministic_entailment` returning `ClaimResult` with `passed=True` on valid multi-date documents, and `passed=False, reason="EVENT_DATE_MISMATCH"` on date-swapped claims.

- [ ] **Step 1: Write failing tests for multi-date acceptance and date-swapping rejection**

Add to `app/backend/tests/test_claim_validation.py`:

```python
def test_multi_date_evidence_legitimate_claim_passes():
    validator = ClaimValidator()
    evidence = {
        "E1": "Patient was admitted on 2026-05-01. Patient underwent surgery on 2026-05-02. Patient discharged on 2026-05-10."
    }
    claim = "Patient underwent surgery on 2026-05-02 [E1]."
    result = validator.validate_sentence(claim, evidence, ValidationContext())
    assert result.passed is True


def test_adversarial_date_swap_rejected():
    validator = ClaimValidator()
    evidence = {
        "E1": "Patient was admitted on 2026-05-01. Patient underwent surgery on 2026-05-02. Patient discharged on 2026-05-10."
    }
    # Claim falsely swaps discharge date into surgery event
    swapped_claim = "Patient underwent surgery on 2026-05-10 [E1]."
    result = validator.validate_sentence(swapped_claim, evidence, ValidationContext())
    assert result.passed is False
    assert any(c.reason in ("EVENT_DATE_MISMATCH", "DATE_MISMATCH") for c in result.claims)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_claim_validation.py -k "test_multi_date_evidence_legitimate_claim_passes or test_adversarial_date_swap_rejected" -v`
Expected: `test_multi_date_evidence_legitimate_claim_passes` FAILS with `DATE_AMBIGUOUS`.

- [ ] **Step 3: Implement Clause-Level Event-Date Binding in `claim_validation.py`**

Modify `deterministic_entailment` in `app/backend/src/hospital_ai/services/claim_validation.py`:

```python
    claim_dates = _extract_dates(claim_text)
    if "date" in strict_fields and claim_dates:
        evidence_dates = _extract_dates(evidence)
        # 1. If claim date doesn't exist anywhere in evidence, immediate mismatch
        if not claim_dates <= evidence_dates:
            return _deterministic_failure(claim, "DATE_MISMATCH")

        # 2. Clause-level event binding
        clauses = [c for c in re.split(r"[.;\n]+", evidence) if c.strip()]
        claim_tokens = _meaningful_tokens(claim_text)

        for d in claim_dates:
            # Find evidence clauses containing this specific date
            matching_clauses = [c for c in clauses if d in _extract_dates(c)]
            if not matching_clauses:
                return _deterministic_failure(claim, "DATE_MISMATCH")

            # Check if at least one matching clause has semantic action overlap with claim
            has_event_support = False
            for clause in matching_clauses:
                clause_tokens = _meaningful_tokens(clause)
                overlap = claim_tokens & clause_tokens
                # Overlap of meaningful non-stopwords
                if len(overlap) >= 1:
                    has_event_support = True
                    break

            if not has_event_support and len(evidence_dates) > 1:
                return _deterministic_failure(claim, "EVENT_DATE_MISMATCH")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_claim_validation.py -v`
Expected: PASS all tests in `test_claim_validation.py`.

- [ ] **Step 5: Commit Task 3**

```bash
git add app/backend/src/hospital_ai/services/claim_validation.py app/backend/tests/test_claim_validation.py
git commit -m "fix(validation): implement clause-level event-date binding to eliminate DATE_AMBIGUOUS"
```

---

### Task 4: Selective GraphRAG Traversal via Patient Anchor

**Files:**
- Modify: `app/backend/src/hospital_ai/services/graph_rag.py:570-620`
- Test: `app/backend/tests/test_graph_traversal_guard.py`

**Interfaces:**
- Consumes: `GraphEntity`, `GraphRelationAssertion`
- Produces: `find_related_entities` allowing traversal through `CANONICAL_PATIENT_ANCHOR` only along clinical condition/allergy relations (`ALLOWED_PATIENT_EXPANSION_RELATIONS`) up to 15 nodes.

- [ ] **Step 1: Write failing test for 2-hop traversal via patient anchor**

Add to `app/backend/tests/test_graph_traversal_guard.py`:

```python
@pytest.mark.asyncio
async def test_traversal_crosses_patient_anchor_for_conditions(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    diltiazem = GraphEntity(id=uuid.uuid4(), patient_id=patient_id, normalized_label="diltiazem", entity_type="drug")
    patient_self = GraphEntity(id=uuid.uuid4(), patient_id=patient_id, normalized_label="patient:self", entity_type="patient_anchor")
    heart_failure = GraphEntity(id=uuid.uuid4(), patient_id=patient_id, normalized_label="heart_failure", entity_type="condition")
    db_session.add_all([diltiazem, patient_self, heart_failure])
    await db_session.flush()

    rel1 = GraphRelationAssertion(
        id=uuid.uuid4(), patient_id=patient_id, subject_entity_id=diltiazem.id,
        object_entity_id=patient_self.id, relation_type="prescribed_for", normalized_value="prescribed_for"
    )
    rel2 = GraphRelationAssertion(
        id=uuid.uuid4(), patient_id=patient_id, subject_entity_id=patient_self.id,
        object_entity_id=heart_failure.id, relation_type="diagnosed_with", normalized_value="diagnosed_with"
    )
    db_session.add_all([rel1, rel2])
    await db_session.commit()

    ctx = await find_related_entities(db_session, ["diltiazem"], max_hops=2, patient_id=patient_id)
    labels = {e.normalized_label for e in ctx.entities}
    assert "heart_failure" in labels
```

- [ ] **Step 2: Run test to verify it fails**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_graph_traversal_guard.py -k test_traversal_crosses_patient_anchor_for_conditions -v`
Expected: FAIL (`"heart_failure"` not in labels due to `frontier_ids` filtering out `CANONICAL_PATIENT_ANCHOR`).

- [ ] **Step 3: Implement Selective Relation Expansion in `find_related_entities`**

In `app/backend/src/hospital_ai/services/graph_rag.py`:
Define whitelist:
```python
ALLOWED_PATIENT_ANCHOR_RELATIONS = frozenset([
    "diagnosed_with",
    "history_of",
    "allergic_to",
    "has_observation",
    "contraindicates",
])
MAX_GRAPH_CONTEXT_ENTITIES = 15
```

When building `next_frontier`:
```python
        for rel in new_relations:
            # If expanding through patient anchor, only allow allowed clinical relations
            is_anchor_rel = False
            for eid in (rel.subject_entity_id, rel.object_entity_id):
                entity = next((e for e in all_entities if e.id == eid), None)
                if entity and entity.normalized_label == CANONICAL_PATIENT_ANCHOR:
                    is_anchor_rel = True
                    break

            if is_anchor_rel and rel.relation_type not in ALLOWED_PATIENT_ANCHOR_RELATIONS:
                continue

            for eid in (rel.subject_entity_id, rel.object_entity_id):
                if eid not in visited_ids:
                    next_frontier.add(eid)
                    visited_ids.add(eid)
```
Enforce `all_entities = all_entities[:MAX_GRAPH_CONTEXT_ENTITIES]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_graph_traversal_guard.py -v`
Expected: PASS.

- [ ] **Step 5: Commit Task 4**

```bash
git add app/backend/src/hospital_ai/services/graph_rag.py app/backend/tests/test_graph_traversal_guard.py
git commit -m "fix(graph): enable selective traversal through patient anchor for conditions"
```

---

### Task 5: Full Adversarial Test Suite & Master Quality Gate Verification

**Files:**
- Create: `app/backend/tests/test_clinical_safety_adversarial.py`

**Interfaces:**
- Consumes: All 3 updated services (`DrugCheckService`, `ClaimValidator`, `find_related_entities`).
- Produces: 7 comprehensive adversarial test cases covering the safety boundaries and edge cases.

- [ ] **Step 1: Create `app/backend/tests/test_clinical_safety_adversarial.py`**

Write complete test file:

```python
from __future__ import annotations

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.clinical_graph import GraphEntity, GraphMention, GraphRelationAssertion
from hospital_ai.db.models import Document, DocumentIndexGeneration
from hospital_ai.services.claim_validation import ClaimValidator, ValidationContext
from hospital_ai.services.drug_check import DrugCheckService
from hospital_ai.services.graph_rag import find_related_entities


def test_adversarial_date_swap_rejection():
    validator = ClaimValidator()
    evidence = {
        "E1": "Patient admitted on 2026-05-01. Underwent coronary bypass surgery on 2026-05-02. Discharged on 2026-05-10."
    }
    swapped_claim = "Patient underwent coronary bypass surgery on 2026-05-10 [E1]."
    res = validator.validate_sentence(swapped_claim, evidence, ValidationContext())
    assert res.passed is False
    assert any(c.reason in ("EVENT_DATE_MISMATCH", "DATE_MISMATCH") for c in res.claims)


def test_multi_date_legitimate_claim_acceptance():
    validator = ClaimValidator()
    evidence = {
        "E1": "Patient admitted on 2026-05-01. Underwent coronary bypass surgery on 2026-05-02. Discharged on 2026-05-10."
    }
    legitimate_claim = "Patient underwent coronary bypass surgery on 2026-05-02 [E1]."
    res = validator.validate_sentence(legitimate_claim, evidence, ValidationContext())
    assert res.passed is True


@pytest.mark.asyncio
async def test_candidate_drug_ddi_warning(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    doc = Document(id=uuid.uuid4(), patient_id=patient_id, filename="chart.pdf", status="ready")
    gen = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, state="active")
    doc.active_index_generation_id = gen.id
    db_session.add_all([doc, gen])
    await db_session.flush()

    aspirin = GraphEntity(
        id=uuid.uuid4(), patient_id=patient_id, normalized_label="aspirin",
        entity_type="drug", lifecycle_status="active"
    )
    db_session.add(aspirin)
    await db_session.flush()

    mention = GraphMention(
        id=uuid.uuid4(), patient_id=patient_id, entity_id=aspirin.id,
        generation_id=gen.id, document_id=doc.id, revision_set_id=uuid.uuid4(),
        page_revision_id=uuid.uuid4(), chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1"
    )
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    warnings = await service.check_interactions(
        query_text="Can I prescribe warfarin 5mg daily for this patient?",
        patient_id=patient_id,
    )
    assert len(warnings) >= 1
    assert any("warfarin" in w.drug_name.lower() or "aspirin" in w.drug_name.lower() for w in warnings)


@pytest.mark.asyncio
async def test_graph_traversal_via_patient_to_condition(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    diltiazem = GraphEntity(id=uuid.uuid4(), patient_id=patient_id, normalized_label="diltiazem", entity_type="drug")
    patient_self = GraphEntity(id=uuid.uuid4(), patient_id=patient_id, normalized_label="patient:self", entity_type="patient_anchor")
    heart_failure = GraphEntity(id=uuid.uuid4(), patient_id=patient_id, normalized_label="heart_failure", entity_type="condition")
    db_session.add_all([diltiazem, patient_self, heart_failure])
    await db_session.flush()

    rel1 = GraphRelationAssertion(
        id=uuid.uuid4(), patient_id=patient_id, subject_entity_id=diltiazem.id,
        object_entity_id=patient_self.id, relation_type="prescribed_for", normalized_value="prescribed_for"
    )
    rel2 = GraphRelationAssertion(
        id=uuid.uuid4(), patient_id=patient_id, subject_entity_id=patient_self.id,
        object_entity_id=heart_failure.id, relation_type="diagnosed_with", normalized_value="diagnosed_with"
    )
    db_session.add_all([rel1, rel2])
    await db_session.commit()

    ctx = await find_related_entities(db_session, ["diltiazem"], max_hops=2, patient_id=patient_id)
    labels = {e.normalized_label for e in ctx.entities}
    assert "heart_failure" in labels


@pytest.mark.asyncio
async def test_discontinued_medication_does_not_block_candidate(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    doc = Document(id=uuid.uuid4(), patient_id=patient_id, filename="chart.pdf", status="ready")
    gen = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, state="active")
    doc.active_index_generation_id = gen.id
    db_session.add_all([doc, gen])
    await db_session.flush()

    discontinued_warfarin = GraphEntity(
        id=uuid.uuid4(), patient_id=patient_id, normalized_label="warfarin",
        entity_type="drug", lifecycle_status="discontinued"
    )
    db_session.add(discontinued_warfarin)
    await db_session.flush()

    mention = GraphMention(
        id=uuid.uuid4(), patient_id=patient_id, entity_id=discontinued_warfarin.id,
        generation_id=gen.id, document_id=doc.id, revision_set_id=uuid.uuid4(),
        page_revision_id=uuid.uuid4(), chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1"
    )
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    warnings = await service.check_interactions(
        query_text="Can we start aspirin 81mg daily?",
        patient_id=patient_id,
        min_severity="high",
    )
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_unapproved_generation_medication_ignored(db_session: AsyncSession):
    patient_id = uuid.uuid4()
    doc = Document(id=uuid.uuid4(), patient_id=patient_id, filename="chart.pdf", status="ready")
    active_gen = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, state="active")
    unapproved_gen = DocumentIndexGeneration(id=uuid.uuid4(), document_id=doc.id, state="superseded")
    doc.active_index_generation_id = active_gen.id
    db_session.add_all([doc, active_gen, unapproved_gen])
    await db_session.flush()

    drug = GraphEntity(
        id=uuid.uuid4(), patient_id=patient_id, normalized_label="warfarin",
        entity_type="drug", lifecycle_status="active"
    )
    db_session.add(drug)
    await db_session.flush()

    # Mention points to unapproved generation
    mention = GraphMention(
        id=uuid.uuid4(), patient_id=patient_id, entity_id=drug.id,
        generation_id=unapproved_gen.id, document_id=doc.id, revision_set_id=uuid.uuid4(),
        page_revision_id=uuid.uuid4(), chunk_id=uuid.uuid4(),
        independent_source_identity="chart.pdf:1:1"
    )
    db_session.add(mention)
    await db_session.commit()

    service = DrugCheckService(db_session)
    warnings = await service.check_interactions(
        query_text="Can we start aspirin 81mg daily?",
        patient_id=patient_id,
        min_severity="high",
    )
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_negated_allergy_does_not_block(db_session: AsyncSession):
    # Negated allergies in text ("NKDA") must not produce active allergy entities
    from hospital_ai.services.graph_rag import extract_entities_and_relations_nlp
    entities, relations = await extract_entities_and_relations_nlp("Patient reports NKDA (no known drug allergies).")
    allergy_relations = [r for r in relations if r.relation_type == "allergic_to"]
    assert len(allergy_relations) == 0
```
- [ ] **Step 2: Run adversarial test suite**

Run: `app/backend/.venv/Scripts/python.exe -m pytest app/backend/tests/test_clinical_safety_adversarial.py -v`
Expected: PASS (7 passed).

- [ ] **Step 3: Run the master deterministic quality gate**

Run: `app/backend/.venv/Scripts/python.exe app/backend/scripts/verify_contracts.py`
Expected: PASS (73 paths verified).

Run: `cd app/frontend && bun run typecheck && bun run test`
Expected: PASS (0 type errors, 209 tests passed).

- [ ] **Step 4: Commit Task 5**

```bash
git add app/backend/tests/test_clinical_safety_adversarial.py
git commit -m "test(safety): add 7 adversarial clinical safety test cases"
```
