"""Add threaded issue comments.

Revision ID: 20261119_04
Revises: 20261118_03
Create Date: 2026-11-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261119_04"
down_revision: Union[str, None] = "20261118_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "issue_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_id"], ["issue_comments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_issue_comments_id"), "issue_comments", ["id"], unique=False)
    op.create_index(op.f("ix_issue_comments_issue_id"), "issue_comments", ["issue_id"], unique=False)
    op.create_index(op.f("ix_issue_comments_author_id"), "issue_comments", ["author_id"], unique=False)
    op.create_index(op.f("ix_issue_comments_parent_id"), "issue_comments", ["parent_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_issue_comments_parent_id"), table_name="issue_comments")
    op.drop_index(op.f("ix_issue_comments_author_id"), table_name="issue_comments")
    op.drop_index(op.f("ix_issue_comments_issue_id"), table_name="issue_comments")
    op.drop_index(op.f("ix_issue_comments_id"), table_name="issue_comments")
    op.drop_table("issue_comments")
