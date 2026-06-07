# Non-Functional Requirements

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Status: Draft  
> Owner: Product Owner / Business Analyst  
> Last Updated: 2026-06-07  

---

## Non-Functional Requirements Catalog

| NFR ID | Category | Requirement | Target | Verification |
|---|---|---|---|---|
| NFR-PERF-001 | Performance | Patient summary latency | <30 sec MVP | Perf test |
| NFR-PERF-002 | Performance | Document search latency | P95 <5 sec | Load test |
| NFR-SEC-001 | Security | All APIs authenticated | 100% endpoints | Security test |
| NFR-SEC-002 | Security | No unauthorized context to LLM | 0 leaks | Access test |
| NFR-PRI-001 | Privacy | No external LLM for PHI by default | Local mode | Architecture review |
| NFR-AUD-001 | Audit | Sensitive access logged | 100% | Audit sample |
| NFR-OBS-001 | Observability | Logs, metrics, traces | Trace ID across flow | Ops review |
| NFR-REL-001 | Reliability | OCR/index jobs retryable | Retry succeeds | Integration test |
| NFR-COST-001 | Cost | MVP runs on 16GB RAM | Local Lite works | Dev test |

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-27 | Product Owner | Initial flat requirements draft |
| 2.0 | 2026-06-07 | Agent | Split non-functional requirements into a dedicated document |
