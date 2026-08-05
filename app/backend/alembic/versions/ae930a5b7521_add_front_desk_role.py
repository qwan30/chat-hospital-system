"""add_front_desk_role

Revision ID: ae930a5b7521
Revises: 60e7683f03bd
Create Date: 2026-06-21 19:51:54.072972

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ae930a5b7521"
down_revision: Union[str, None] = "60e7683f03bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("ck_users_role", type_="check")
        batch_op.create_check_constraint(
            "ck_users_role",
            "role in ('doctor','nurse','pharmacist','lab_staff','records_staff','security','admin','front_desk')",
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("ck_users_role", type_="check")
        batch_op.create_check_constraint(
            "ck_users_role", "role in ('doctor','nurse','pharmacist','lab_staff','records_staff','security','admin')"
        )
