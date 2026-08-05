"""update ck_documents_status

Revision ID: 13dde695c97d
Revises: 8d6cedbd7e08
Create Date: 2026-07-31 23:27:10.231630

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "13dde695c97d"
down_revision: Union[str, None] = "8d6cedbd7e08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_constraint("ck_documents_status", type_="check")
        batch_op.create_check_constraint(
            "ck_documents_status",
            "status in ('uploaded','queued','processing','review_required','ready_with_warnings','ready','failed','cancelled','quarantined','soft_deleted')",  # noqa: E501
        )
    with op.batch_alter_table("document_processing_events", schema=None) as batch_op:
        batch_op.drop_constraint("ck_document_processing_event_stage", type_="check")
        batch_op.create_check_constraint(
            "ck_document_processing_event_stage",
            "stage in ('upload','ocr','index','ready','preflight_document','classify_document','extract_native_pages','extract_vision_pages','reconstruct_document','extract_clinical_facts','validate_and_route_review','build_fhir_draft','index_document','extract_graph','run_cdss','finalize_document')",  # noqa: E501
        )


def downgrade() -> None:
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_constraint("ck_documents_status", type_="check")
        batch_op.create_check_constraint(
            "ck_documents_status",
            "status in ('uploaded','ocr_processing','ocr_failed','ocr_completed','indexing','index_failed','indexed','archived')",  # noqa: E501
        )
    with op.batch_alter_table("document_processing_events", schema=None) as batch_op:
        batch_op.drop_constraint("ck_document_processing_event_stage", type_="check")
        batch_op.create_check_constraint(
            "ck_document_processing_event_stage", "stage in ('upload','ocr','index','ready')"
        )
