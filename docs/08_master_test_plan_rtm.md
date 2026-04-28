# Master Test Plan & RTM

**Project:** AI-Powered Hospital Knowledge Assistant
**Project Code:** HOSP-AI-001
**Version:** 1.0
**Status:** Draft
**Last Updated:** 2026-04-27

**Owner:** QA Lead / PM

## 1. Test Strategy
| Item | Content |
|---|---|
| Objective | Verify functional, security, privacy, performance, retrieval quality, and impact metrics. |
| Scope | Unit, integration, API, system, UAT, security smoke, OCR, RAG evaluation. |
| Out of Scope | Medical device certification, full penetration test, clinical efficacy validation. |
| Safety Principle | AI answers must be cited and assistive only. |

## 2. Test Levels
| Level | Objective | Owner | Evidence |
|---|---|---|---|
| Unit | Verify modules/functions | Dev | Coverage report |
| Integration | API + DB + Redis + workers | Dev/QA | Test run |
| Permission | RBAC/ABAC and retrieval filters | QA/Security | Access report |
| OCR | OCR output and indexing | QA/AI | OCR sample report |
| RAG Eval | Relevance, citations, safe refusal | QA/AI | Eval report |
| System | End-to-end workflows | QA | Test cases |
| UAT | Business validation | PO/SME | Sign-off |
| Performance | Latency and load | QA/SRE | Load report |

## 3. Entry / Exit Criteria
| Stage | Entry | Exit |
|---|---|---|
| System Test | Build deployed, test data ready | No P0/P1, pass >=95% |
| UAT | System test exit met | UAT sign-off |
| Demo/Release | UAT passed, rollback ready | Smoke pass, metrics captured |

## 4. Test Case Inventory
| TC ID | Title | Linked Req | Priority | Expected Result |
|---|---|---|---|---|
| TC-001 | Login succeeds | FR-001 | P1 | User receives session |
| TC-002 | Unauthorized patient blocked | FR-002 | P1 | 403 + audit event |
| TC-003 | Patient search scoped | FR-003 | P1 | Unauthorized patients excluded |
| TC-004 | AI chat cited answer | FR-004/005 | P1 | Answer includes citations |
| TC-005 | Safe refusal without evidence | BR-AI-001 | P1 | Insufficient evidence response |
| TC-006 | Upload creates OCR job | FR-006 | P1 | Status processing |
| TC-007 | OCR document searchable | FR-006/007 | P1 | Chunks indexed |
| TC-008 | Summary under target | FR-008 | P1 | <30 sec MVP dataset |
| TC-009 | Summary required sections | FR-008 | P1 | History, meds, allergies, labs |
| TC-010 | Metric created after query | FR-009 | P1 | Metric event stored |
| TC-011 | Audit created after query | FR-010 | P1 | Audit event stored |
| TC-012 | Graph query works | FR-011 | P2 | Relationship evidence used |
| TC-013 | Drug/allergy warning | FR-012 | P2 | Warning + evidence |
| TC-014 | Timeline filters | FR-013 | P2 | Correct entries displayed |
| TC-015 | Local stack on 16GB | NFR-COST-001 | P1 | Local Lite runs |
| TC-016 | Unauthorized chunks not passed to LLM | NFR-SEC-002 | P1 | 0 leakage |
| TC-017 | HMS appointment evidence import | FR-004/005 | P1 | Imported appointment summary cites only after patient permission |
| TC-018 | HMS appointment ownership mismatch blocked | NFR-SEC-002 | P1 | Import rejected before indexing |
| TC-019 | Deleted HMS source excluded | NFR-SEC-002 | P1 | Archived/deleted HMS-derived document is not retrieved |

## 5. RTM
| Req ID | Design Ref | API/DB Ref | Test Cases | Status |
|---|---|---|---|---|
| FR-001 | Auth component | API-001, users | TC-001 | Covered |
| FR-002 | Permission service | roles, access matrix | TC-002, TC-003, TC-016 | Covered |
| FR-004/005 | Chat + citation UI | API-005, retrieved_evidence | TC-004, TC-005 | Covered |
| FR-004/005-HMS | HMS appointment evidence | API-010, documents, document_chunks | TC-017, TC-018, TC-019 | Covered |
| FR-006/007 | OCR/doc search | API-006/007, document_chunks | TC-006, TC-007 | Covered |
| FR-008 | Patient summary | API-004 | TC-008, TC-009 | Covered |
| FR-009 | Metrics dashboard | API-011, metric_events | TC-010 | Covered |
| FR-010 | Audit log | API-010, audit_events | TC-011 | Covered |
| FR-011 | Graph RAG | graph_edges/Neo4j | TC-012 | Partial |
| FR-012 | Drug check | API-009 | TC-013 | Partial |
| NFR-COST-001 | Local Lite deployment | docker/local scripts | TC-015 | Covered |

## 6. AI/RAG Evaluation Metrics
| Metric | Target |
|---|---|
| Citation rate when evidence exists | >=95% |
| Claims supported by citations | >=90% |
| Top-k retrieval contains correct evidence | >=80% |
| Safe refusal when no evidence | >=90% |
| Unauthorized chunks passed to LLM | 0 |
| Patient summary latency | <30 sec |

## 7. UAT Scenarios
| Scenario | SME | Sign-off |
|---|---|---|
| Doctor generates patient summary and verifies citations | TBD | [ ] |
| Nurse searches latest patient document | TBD | [ ] |
| Records staff uploads scanned document | TBD | [ ] |
| Pharmacist reviews drug/allergy warning | TBD | [ ] |
| Security reviews audit log | TBD | [ ] |
| PM reviews time/cost metrics | TBD | [ ] |
