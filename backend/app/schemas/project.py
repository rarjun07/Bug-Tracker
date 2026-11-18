from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ProjectRole(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    key: str = Field(min_length=2, max_length=10, pattern=r"^[A-Z][A-Z0-9]+$")
    description: str | None = Field(default=None, max_length=5000)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key: str
    description: str | None
    created_by_id: int
    created_at: datetime


class ProjectMemberCreate(BaseModel):
    identity: str = Field(min_length=1, max_length=320, description="Username or email")
    role: ProjectRole = ProjectRole.DEVELOPER


class ProjectMemberRoleUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberRead(BaseModel):
    user_id: int
    username: str
    email: str
    role: ProjectRole
    joined_at: datetime
