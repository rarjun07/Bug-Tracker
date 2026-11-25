from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.project import Project
from app.models.user import User


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("project_id", "issue_number", name="uq_issues_project_number"),
        CheckConstraint(
            "issue_type IN ('bug', 'task', 'feature')", name="ck_issues_issue_type"
        ),
        CheckConstraint(
            "status IN ('todo', 'in_progress', 'done')", name="ck_issues_status"
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')", name="ck_issues_priority"
        ),
        Index("ix_issues_project_status", "project_id", "status"),
        Index("ix_issues_project_type", "project_id", "issue_type"),
        Index("ix_issues_project_priority", "project_id", "priority"),
        Index("ix_issues_project_assignee", "project_id", "assignee_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_type: Mapped[str] = mapped_column(String(20), nullable=False, default="bug")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="todo", server_default="todo"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", server_default="medium"
    )
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="issues")
    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    comments: Mapped[list["IssueComment"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )
