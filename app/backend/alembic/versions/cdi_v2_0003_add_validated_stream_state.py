"""add_validated_stream_state

Revision ID: cdi_v2_0003
Revises: cdi_v2_0002
Create Date: 2026-08-05 12:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cdi_v2_0003"
down_revision: Union[str, None] = "cdi_v2_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add validation_mode column to ai_queries (nullable for historical rows)
    op.add_column("ai_queries", sa.Column("validation_mode", sa.String(length=64), nullable=True))
    # Add last_emitted_sequence column (defaults to 0 for historical rows)
    op.add_column("ai_queries", sa.Column("last_emitted_sequence", sa.Integer(), nullable=True, server_default="0"))
    # The 'interrupted' status is now allowed alongside existing statuses.
    # No constraint rewrite needed — the status column is a plain String(32)
    # without a CHECK constraint, so 'interrupted' is already storable.


def downgrade() -> None:
    op.drop_column("ai_queries", "last_emitted_sequence")
    op.drop_column("ai_queries", "validation_mode")
