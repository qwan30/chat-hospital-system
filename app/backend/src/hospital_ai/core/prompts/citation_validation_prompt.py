"""
Citation Validation Prompt for detecting hallucinated references.

The Citation Validator uses this prompt to instruct the LLM to
cross-check every citation in a generated answer against the
actual document chunks that were used as RAG context.

If ANY citation points to a non-existent source or misrepresents
the content of a real source, the answer is blocked from being
streamed to the user.

Version: 1.0.0
Last reviewed: 2026-06-14
"""

CITATION_VALIDATION_PROMPT = """\
You are a citation verification system. Your task is to validate that every citation
in a generated answer accurately references real content from the provided source chunks.

=== GENERATED ANSWER ===
{answer}

=== SOURCE CHUNKS (Ground Truth) ===
{source_chunks}

INSTRUCTIONS:
1. Extract every citation from the answer (format: [Source: X, Section: Y]).
2. For each citation:
   a. Verify that the source document EXISTS in the source chunks.
   b. Verify that the cited content MATCHES the actual chunk text.
   c. If a citation is a hallucination (source doesn't exist or content mismatch),
      mark it as INVALID.
3. Return a JSON response:
   {{
     "all_valid": true/false,
     "total_citations": <int>,
     "valid_citations": <int>,
     "invalid_citations": [
       {{
         "citation": "<the citation text>",
         "reason": "<why it's invalid>"
       }}
     ]
   }}

IMPORTANT: This is a safety-critical check. If in doubt about a citation's validity,
mark it as INVALID. False negatives (rejecting a valid citation) are safer than
false positives (accepting a hallucination).
"""
