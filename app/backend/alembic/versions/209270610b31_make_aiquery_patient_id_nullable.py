"""Make AiQuery.patient_id nullable

Revision ID: 209270610b31
Revises: 0008_add_pending_info_status
Create Date: 2026-06-20 20:07:55.354002

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "209270610b31"
down_revision: Union[str, None] = "0008_add_pending_info_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("ai_queries") as batch_op:
        batch_op.alter_column("patient_id", existing_type=sa.Uuid(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("ai_queries") as batch_op:
        batch_op.alter_column("patient_id", existing_type=sa.Uuid(), nullable=False)
