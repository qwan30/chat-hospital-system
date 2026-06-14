"""
Centralized Prompt Registry for Hospital AI.

All LLM system prompts and instruction templates are versioned here
rather than hardcoded in application services. This provides:

1. **Single source of truth** — change a prompt once, affect all callers.
2. **Version control** — prompt changes are tracked in git alongside code.
3. **Testability** — prompts can be unit-tested for expected behavior.
4. **Prompt drift monitoring** — centralized registry makes it easy to
   compare prompt versions and A/B test variations.

Architecture principle:
    Prompts are domain logic, NOT configuration. They encode clinical
    safety rules and citation requirements. They belong in core/,
    not in environment variables or service-layer string literals.
"""

from hospital_ai.core.prompts.rag_system_prompt import RAG_SYSTEM_PROMPT, CLINICAL_RAG_TEMPLATE
from hospital_ai.core.prompts.citation_validation_prompt import CITATION_VALIDATION_PROMPT
from hospital_ai.core.prompts.patient_summary_prompt import PATIENT_SUMMARY_PROMPT, PATIENT_SUMMARY_TEMPLATE
from hospital_ai.core.prompts.drug_check_prompt import DRUG_ALLERGY_CHECK_PROMPT

__all__ = [
    "RAG_SYSTEM_PROMPT",
    "CLINICAL_RAG_TEMPLATE",
    "CITATION_VALIDATION_PROMPT",
    "PATIENT_SUMMARY_PROMPT",
    "PATIENT_SUMMARY_TEMPLATE",
    "DRUG_ALLERGY_CHECK_PROMPT",
]
