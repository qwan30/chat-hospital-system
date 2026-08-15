from __future__ import annotations

import pytest

from hospital_ai.services.capabilities import role_has_capability


@pytest.mark.parametrize(
    ("role", "capability", "allowed"),
    [
        ("doctor", "document_revision.edit", True),
        ("doctor", "document_revision.approve", False),
        ("records_staff", "document_revision.restore", True),
        ("admin", "document_revision.edit", False),
        ("admin", "document_revision.view_raw", True),
        ("admin", "document_revision.approve", True),
        ("security", "document_revision.view_raw", False),
    ],
)
def test_default_capability_matrix(role: str, capability: str, allowed: bool) -> None:
    assert role_has_capability(role, capability) is allowed
