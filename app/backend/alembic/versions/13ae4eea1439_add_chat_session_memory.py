"""add_chat_session_memory

Revision ID: 13ae4eea1439
Revises: 0006_add_phase4_tables
Create Date: 2026-06-20 00:24:17.647462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13ae4eea1439'
down_revision: Union[str, None] = '0006_add_phase4_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('access_requests',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('patient_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('justification', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('reviewed_by_user_id', sa.Uuid(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("status in ('pending','approved','denied')", name='ck_access_requests_status'),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('access_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_access_requests_patient_id'), ['patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_access_requests_user_id'), ['user_id'], unique=False)

    op.create_table('chat_session_memory',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('thread_id', sa.Uuid(), nullable=False),
    sa.Column('active_patient_id', sa.Uuid(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('active_entities', sa.JSON(), nullable=False),
    sa.Column('source_ids', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['active_patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('chat_session_memory', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_chat_session_memory_active_patient_id'), ['active_patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_chat_session_memory_thread_id'), ['thread_id'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('chat_session_memory', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_chat_session_memory_thread_id'))
        batch_op.drop_index(batch_op.f('ix_chat_session_memory_active_patient_id'))

    op.drop_table('chat_session_memory')
    with op.batch_alter_table('access_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_access_requests_user_id'))
        batch_op.drop_index(batch_op.f('ix_access_requests_patient_id'))

    op.drop_table('access_requests')
