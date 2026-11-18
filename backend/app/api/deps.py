from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.project import ProjectMember
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    settings = get_settings()
    secret_key = settings.jwt_secret_key.get_secret_value()
    if len(secret_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise credentials_error
        user_id = int(subject)
    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_error from None

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise credentials_error
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def get_project_member(
    project_id: int,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProjectMember:
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if member is None:
        # Hide projects from users who have not been added to their team.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return member


def get_project_admin(
    member: Annotated[ProjectMember, Depends(get_project_member)],
) -> ProjectMember:
    if member.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project admin role required",
        )
    return member


CurrentUser = Annotated[User, Depends(get_current_user)]
ProjectMemberAccess = Annotated[ProjectMember, Depends(get_project_member)]
ProjectAdmin = Annotated[ProjectMember, Depends(get_project_admin)]
