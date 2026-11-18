from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IssueType(StrEnum):
    BUG = "bug"
    TASK = "task"
    FEATURE = "feature"


class IssueStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class IssuePriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class IssueCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    issue_type: IssueType = IssueType.BUG
    priority: IssuePriority = IssuePriority.MEDIUM
    assignee_id: int | None = None

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title cannot be blank")
        return value


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    issue_type: IssueType | None = None
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee_id: int | None = None

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("title cannot be blank")
        return value


class IssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_key: str
    project_id: int
    issue_number: int
    title: str
    description: str | None
    issue_type: IssueType
    status: IssueStatus
    priority: IssuePriority
    reporter_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
