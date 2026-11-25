"""Add indexes for project issue filters.

Revision ID: 20261125_05
Revises: 20261119_04
Create Date: 2026-11-25
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20261125_05"
down_revision: Union[str, None] = "20261119_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_issues_project_type", "issues", ["project_id", "issue_type"])
    op.create_index("ix_issues_project_priority", "issues", ["project_id", "priority"])
    op.create_index("ix_issues_project_assignee", "issues", ["project_id", "assignee_id"])


def downgrade() -> None:
    op.drop_index("ix_issues_project_assignee", table_name="issues")
    op.drop_index("ix_issues_project_priority", table_name="issues")
    op.drop_index("ix_issues_project_type", table_name="issues")
