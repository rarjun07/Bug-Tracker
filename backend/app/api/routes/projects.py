from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession, ProjectAdmin, ProjectMemberAccess
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberRoleUpdate,
    ProjectRead,
    ProjectRole,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _member_read(member: ProjectMember) -> ProjectMemberRead:
    return ProjectMemberRead(
        user_id=member.user_id,
        username=member.user.username,
        email=member.user.email,
        role=member.role,
        joined_at=member.joined_at,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: DbSession, current_user: CurrentUser) -> Project:
    project = Project(
        name=project_in.name.strip(),
        key=project_in.key,
        description=project_in.description.strip() if project_in.description else None,
        created_by_id=current_user.id,
    )
    db.add(project)
    try:
        db.flush()
        db.add(
            ProjectMember(
                project_id=project.id,
                user_id=current_user.id,
                role=ProjectRole.ADMIN.value,
            )
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with this key already exists",
        ) from None
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(db: DbSession, current_user: CurrentUser) -> list[Project]:
    return list(
        db.scalars(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == current_user.id)
            .order_by(Project.created_at.desc(), Project.id.desc())
        ).all()
    )


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project: ProjectMemberAccess) -> Project:
    return project.project


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
def list_project_members(project: ProjectMemberAccess, db: DbSession) -> list[ProjectMemberRead]:
    members = db.scalars(
        select(ProjectMember)
        .where(ProjectMember.project_id == project.project_id)
        .order_by(ProjectMember.joined_at, ProjectMember.user_id)
    ).all()
    return [_member_read(member) for member in members]


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_project_member(
    member_in: ProjectMemberCreate,
    project: ProjectAdmin,
    db: DbSession,
) -> ProjectMemberRead:
    identity = member_in.identity.strip()
    user = db.scalar(
        select(User).where((User.username == identity) | (User.email == identity.lower()))
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    member = ProjectMember(
        project_id=project.project_id,
        user_id=user.id,
        role=member_in.role.value,
    )
    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        ) from None
    db.refresh(member)
    return _member_read(member)


@router.patch(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberRead,
)
def update_project_member_role(
    user_id: int,
    role_update: ProjectMemberRoleUpdate,
    project: ProjectAdmin,
    db: DbSession,
) -> ProjectMemberRead:
    member = db.get(ProjectMember, (project.project_id, user_id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found")

    if member.role == ProjectRole.ADMIN.value and role_update.role != ProjectRole.ADMIN:
        admin_count = db.scalar(
            select(func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project.project_id,
                ProjectMember.role == ProjectRole.ADMIN.value,
            )
        )
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A project must keep at least one admin",
            )

    member.role = role_update.role.value
    db.commit()
    db.refresh(member)
    return _member_read(member)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(user_id: int, project: ProjectAdmin, db: DbSession) -> None:
    member = db.get(ProjectMember, (project.project_id, user_id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found")
    if member.role == ProjectRole.ADMIN.value:
        admin_count = db.scalar(
            select(func.count())
            .select_from(ProjectMember)
            .where(
                ProjectMember.project_id == project.project_id,
                ProjectMember.role == ProjectRole.ADMIN.value,
            )
        )
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A project must keep at least one admin",
            )
    db.delete(member)
    db.commit()
