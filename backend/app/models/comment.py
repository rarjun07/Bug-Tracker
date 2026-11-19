from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("issue_comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    issue: Mapped["Issue"] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()
    parent: Mapped["IssueComment | None"] = relationship(
        remote_side="IssueComment.id", back_populates="replies"
    )
    replies: Mapped[list["IssueComment"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
