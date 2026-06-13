"""bindings notes report metadata

Revision ID: 20260614_0002
Revises: 20260614_0001
Create Date: 2026-06-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260614_0002"
down_revision: str | None = "20260614_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("report_records", sa.Column("counselor_assistance_created_at", sa.DateTime(), nullable=True))
    op.add_column("report_records", sa.Column("model_name", sa.String(length=120), nullable=True))
    op.add_column("report_records", sa.Column("prompt_version", sa.String(length=40), nullable=True))

    op.create_table(
        "counselor_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("counselor_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["counselor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_counselor_notes_client_id", "counselor_notes", ["client_id"])
    op.create_index("ix_counselor_notes_counselor_id", "counselor_notes", ["counselor_id"])


def downgrade() -> None:
    op.drop_index("ix_counselor_notes_counselor_id", table_name="counselor_notes")
    op.drop_index("ix_counselor_notes_client_id", table_name="counselor_notes")
    op.drop_table("counselor_notes")
    op.drop_column("report_records", "prompt_version")
    op.drop_column("report_records", "model_name")
    op.drop_column("report_records", "counselor_assistance_created_at")
