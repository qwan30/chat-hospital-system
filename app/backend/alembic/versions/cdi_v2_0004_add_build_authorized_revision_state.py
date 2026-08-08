"""allow build-authorized revision sets

Revision ID: cdi_v2_0005
Revises: cdi_v2_0004
Create Date: 2026-08-05 18:00:00.000000
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "cdi_v2_0005"
down_revision: Union[str, None] = "cdi_v2_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("document_revision_sets") as batch_op:
        batch_op.drop_constraint("ck_document_revision_sets_status", type_="check")
        batch_op.create_check_constraint(
            "ck_document_revision_sets_status",
            "status in ('submitted','build_authorized','approved','rejected','superseded')",
        )


def downgrade() -> None:
    with op.batch_alter_table("document_revision_sets") as batch_op:
        batch_op.drop_constraint("ck_document_revision_sets_status", type_="check")
        batch_op.create_check_constraint(
            "ck_document_revision_sets_status",
            "status in ('submitted','approved','rejected','superseded')",
        )
