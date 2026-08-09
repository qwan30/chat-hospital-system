"""update access_requests status check constraint

Revision ID: 0008_add_pending_info_status
Revises: 13ae4eea1439
Create Date: 2026-06-20
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_add_pending_info_status"
down_revision: Union[str, None] = "13ae4eea1439"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop constraint and recreate with new status
    with op.batch_alter_table("access_requests", schema=None) as batch_op:
        batch_op.drop_constraint("ck_access_requests_status", type_="check")
        batch_op.create_check_constraint(
            "ck_access_requests_status", "status in ('pending', 'approved', 'denied', 'pending_info')"
        )


def downgrade() -> None:
    with op.batch_alter_table("access_requests", schema=None) as batch_op:
        batch_op.drop_constraint("ck_access_requests_status", type_="check")
        batch_op.create_check_constraint("ck_access_requests_status", "status in ('pending', 'approved', 'denied')")
