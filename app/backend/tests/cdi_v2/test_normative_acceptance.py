import pytest


@pytest.mark.skip(
    reason="CDI v2 normative harness is still a placeholder; keep these scenarios pending implementation."
)
@pytest.mark.parametrize(
    "scenario",
    [
        "stale_if_match",
        "production_self_approval",
        "failed_generation_preserves_active",
        "stale_geometry_not_exact_evidence",
        "canonical_entity_multiple_sources",
        "wrong_patient_and_superseded_filtered",
        "upload_integrity_before_ocr",
        "validated_sse_sequence_and_interrupt",
        "legacy_synthetic_parity",
    ],
)
async def test_normative_acceptance_scenario(scenario, cdi_v2_harness) -> None:
    result = await cdi_v2_harness.run(scenario)
    assert result.passed, (
        f"Invariant Violated: {result.violated_invariant}\n"
        f"Evidence: {result.evidence}"
    )
