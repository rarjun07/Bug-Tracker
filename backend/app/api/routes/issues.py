from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select, update

from app.api.deps import CurrentUser, DbSession, ProjectMemberAccess
from app.models.issue import Issue
from app.models.project import Project, ProjectMember
from app.schemas.issue import IssueCreate, IssueRead, IssueUpdate

router = APIRouter(prefix="/projects/{project_id}/issues", tags=["issues"])


def _issue_read(issue: Issue) -> IssueRead:
    return IssueRead(
        id=issue.id,
        issue_key=f"{issue.project.key}-{issue.issue_number}",
        project_id=issue.project_id,
        issue_number=issue.issue_number,
        title=issue.title,
        description=issue.description,
        issue_type=issue.issue_type,
        status=issue.status,
        priority=issue.priority,
        reporter_id=issue.reporter_id,
        assignee_id=issue.assignee_id,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


def _get_issue(db: DbSession, project_id: int, issue_id: int) -> Issue:
    issue = db.scalar(
        select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id)
    )
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return issue


def _ensure_assignee_is_member(db: DbSession, project_id: int, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    membership = db.get(ProjectMember, (project_id, assignee_id))
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assignee must be a member of this project",
        )


@router.post("", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_in: IssueCreate,
    project_member: ProjectMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> IssueRead:
    project_id = project_member.project_id
    _ensure_assignee_is_member(db, project_id, issue_in.assignee_id)

    # Increment in the database so concurrent creates receive distinct project issue numbers.
    issue_number = db.scalar(
        update(Project)
        .where(Project.id == project_id)
        .values(next_issue_number=Project.next_issue_number + 1)
        .returning(Project.next_issue_number - 1)
    )
    if issue_number is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    issue = Issue(
        project_id=project_id,
        issue_number=issue_number,
        title=issue_in.title.strip(),
        description=issue_in.description.strip() if issue_in.description else None,
        issue_type=issue_in.issue_type.value,
        priority=issue_in.priority.value,
        reporter_id=current_user.id,
        assignee_id=issue_in.assignee_id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return _issue_read(issue)


@router.get("", response_model=list[IssueRead])
def list_issues(
    project_member: ProjectMemberAccess,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[IssueRead]:
    issues = db.scalars(
        select(Issue)
        .where(Issue.project_id == project_member.project_id)
        .order_by(Issue.issue_number.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [_issue_read(issue) for issue in issues]


@router.get("/{issue_id}", response_model=IssueRead)
def read_issue(
    issue_id: int, project_member: ProjectMemberAccess, db: DbSession
) -> IssueRead:
    return _issue_read(_get_issue(db, project_member.project_id, issue_id))


@router.patch("/{issue_id}", response_model=IssueRead)
def update_issue(
    issue_id: int,
    issue_update: IssueUpdate,
    project_member: ProjectMemberAccess,
    db: DbSession,
) -> IssueRead:
    issue = _get_issue(db, project_member.project_id, issue_id)
    changes = issue_update.model_dump(exclude_unset=True)

    for field in ("title", "issue_type", "status", "priority"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )
    if "assignee_id" in changes:
        _ensure_assignee_is_member(db, project_member.project_id, changes["assignee_id"])

    for field, value in changes.items():
        if field == "title" and value is not None:
            value = value.strip()
            if not value:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="title cannot be blank",
                )
        if field in {"issue_type", "status", "priority"} and value is not None:
            value = value.value
        if field == "description" and value is not None:
            value = value.strip() or None
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return _issue_read(issue)


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    issue_id: int, project_member: ProjectMemberAccess, db: DbSession
) -> Response:
    issue = _get_issue(db, project_member.project_id, issue_id)
    db.delete(issue)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
