# BR-006: Graph RAG Relationships

## Metadata
- **ID:** BR-006
- **Status:** draft
- **Owner:** Tech Lead
- **Stakeholders:** Doctor, QA Lead
- **Priority:** Should (Phase 2)
- **Target Quarter:** Post-MVP

## Background
Patient data has natural relationships (patient → encounter → diagnosis → medications → allergies). Graph-based traversal enables richer context retrieval than flat vector search alone, especially for questions like "What medications was the patient on during the encounter that led to diagnosis X?"

## Goal
System supports Graph RAG relationship traversal for patient → encounter → diagnosis → medications → allergy chains.

## Success Metrics
- Relationship-based queries return correct traversal results: ≥80% accuracy
- Graph context improves answer quality over vector-only retrieval: measurable delta

## In Scope
- SQL-based graph edges for MVP
- Neo4j integration in Phase 2
- Patient → encounter → diagnosis → medications → allergy traversal

## Out of Scope
- Multi-hop reasoning across patients
- Knowledge graph construction from unstructured text
- Graph visualization UI

## Related Use Cases
- UC-001: Ask Patient Question (enhanced retrieval)

## Constraints
- **Technical:** Neo4j deferred to Phase 2 (16GB RAM constraint)
- **Performance:** Graph traversal must not exceed overall latency budget

## Open Questions
- [ ] What relationship types beyond clinical data should be supported?
- [ ] Should graph edges be auto-generated or manually curated?

## History
- v1 (2026-04-27, Original): Initial draft
- v2 (2026-06-07, Agent): Extracted to individual file
