"""merge heads

Revision ID: cfb28845ca63
Revises: ae930a5b7521, 68666b884f62
Create Date: 2026-07-16 23:08:41.386566

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfb28845ca63'
down_revision: Union[str, None] = ('ae930a5b7521', '68666b884f62')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
