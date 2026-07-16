from hospital_ai.core.exceptions import EntityNotFoundException


def test_entity_not_found_preserves_metadata_without_constructor_keywords():
    error = EntityNotFoundException("Patient", "patient-123", request_id="trace-456")

    assert error.code == "ENTITY_NOT_FOUND"
    assert error.metadata == {
        "entity_type": "Patient",
        "entity_id": "patient-123",
        "request_id": "trace-456",
    }
