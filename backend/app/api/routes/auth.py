from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import DbSession, get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_unknown_user_password,
)
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: DbSession) -> User:
    normalized_email = str(user_in.email).strip().lower()
    username = user_in.username.strip()
    user = User(
        username=username,
        email=normalized_email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered",
        ) from None
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> Token:
    identity = form_data.username.strip()
    user = db.scalar(
        select(User).where(
            or_(User.username == identity, User.email == identity.lower())
        )
    )
    if user is None:
        verify_unknown_user_password(form_data.password)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
