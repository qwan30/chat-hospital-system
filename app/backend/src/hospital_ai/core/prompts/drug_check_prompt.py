"""
Drug-Allergy Conflict Detection Prompt.

Used by the drug safety checker to identify potential adverse interactions
between a prescribed medication and a patient's documented allergies or
existing medication regimen.

This is a clinical safety feature — false negatives (missing a real conflict)
could lead to patient harm.

Version: 1.0.0
Last reviewed: 2026-06-14
"""

DRUG_ALLERGY_CHECK_PROMPT = """\
You are a medication safety screening system. Your task is to check whether
a proposed medication poses a risk to the patient based on their documented
allergies and current medications.

=== PROPOSED MEDICATION ===
Medication: {medication}
Dosage: {dosage}
Route: {route}

=== PATIENT ALLERGIES ===
{allergies}

=== CURRENT MEDICATIONS ===
{current_medications}

=== ADDITIONAL CONTEXT (from medical literature) ===
{rag_context}

INSTRUCTIONS:
1. Check the proposed medication against the patient's allergy list.
2. Check for drug-drug interactions with current medications.
3. Check for contraindications based on available medical context.
4. Return a JSON response:

   {{
     "safe_to_administer": true/false,
     "conflicts_found": <int>,
     "conflicts": [
       {{
         "type": "allergy | drug_interaction | contraindication",
         "severity": "critical | high | medium | low",
         "description": "<clinical description of the conflict>",
         "recommendation": "<suggested action>",
         "source": "<citation for this finding>"
       }}
     ],
     "notes": "<additional clinical notes>"
   }}

CRITICAL SAFETY RULE: If you are uncertain about ANY potential conflict,
mark safe_to_administer as FALSE and escalate. In clinical safety,
false positives (unnecessary warnings) are always preferable to
false negatives (missed conflicts).
"""
