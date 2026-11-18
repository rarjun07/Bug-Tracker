"""Create issues and project issue numbering.

Revision ID: 20261118_03
Revises: 20261118_02
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261118_03"
down_revision: Union[str, None] = "20261118_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("next_issue_number", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("issue_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("issue_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="todo", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("issue_type IN ('bug', 'task', 'feature')", name="ck_issues_issue_type"),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'done')", name="ck_issues_status"),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name="ck_issues_priority"),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "issue_number", name="uq_issues_project_number"),
    )
    op.create_index(op.f("ix_issues_assignee_id"), "issues", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_issues_id"), "issues", ["id"], unique=False)
    op.create_index(op.f("ix_issues_project_status"), "issues", ["project_id", "status"], unique=False)
    op.create_index(op.f("ix_issues_reporter_id"), "issues", ["reporter_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_issues_reporter_id"), table_name="issues")
    op.drop_index(op.f("ix_issues_project_status"), table_name="issues")
    op.drop_index(op.f("ix_issues_id"), table_name="issues")
    op.drop_index(op.f("ix_issues_assignee_id"), table_name="issues")
    op.drop_table("issues")
    op.drop_column("projects", "next_issue_number")
