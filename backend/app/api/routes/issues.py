from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import String, cast, func, or_, select, update
from sqlalchemy.orm import contains_eager

from app.api.deps import CurrentUser, DbSession, ProjectAdmin, ProjectMemberAccess
from app.models.comment import IssueComment
from app.models.issue import Issue
from app.models.project import Project, ProjectMember
from app.schemas.issue import (
    IssueCommentCreate,
    IssueCommentRead,
    IssueCreate,
    IssueRead,
    IssuePriority,
    IssueStatus,
    IssueType,
    IssueUpdate,
)

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


def _comment_read(comment: IssueComment) -> IssueCommentRead:
    return IssueCommentRead(
        id=comment.id,
        issue_id=comment.issue_id,
        author_id=comment.author_id,
        author_username=comment.author.username,
        parent_id=comment.parent_id,
        content=comment.content,
        created_at=comment.created_at,
    )


def _ensure_assignee_is_member(db: DbSession, project_id: int, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    membership = db.get(ProjectMember, (project_id, assignee_id))
    if membership is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Assignee must be a member of this project",
        )


def _ensure_issue_editor(project_member: ProjectMember) -> None:
    if project_member.role not in {"admin", "developer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or developer role required to modify issues",
        )


@router.post("", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_in: IssueCreate,
    project_member: ProjectMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> IssueRead:
    project_id = project_member.project_id
    _ensure_issue_editor(project_member)
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
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=100)] = None,
    status_filter: Annotated[IssueStatus | None, Query(alias="status")] = None,
    issue_type: IssueType | None = None,
    priority: IssuePriority | None = None,
    assignee_id: Annotated[int | None, Query(ge=1)] = None,
    unassigned: bool = False,
    sort: Annotated[str, Query(pattern="^(newest|oldest)$")] = "newest",
) -> list[IssueRead]:
    conditions = [Issue.project_id == project_member.project_id]
    if search and search.strip():
        term = search.strip()
        issue_key = Project.key.concat("-").concat(cast(Issue.issue_number, String))
        conditions.append(
            or_(
                func.lower(Issue.title).contains(term.lower(), autoescape=True),
                func.lower(Issue.description).contains(term.lower(), autoescape=True),
                func.lower(issue_key).contains(term.lower(), autoescape=True),
            )
        )
    if status_filter is not None:
        conditions.append(Issue.status == status_filter.value)
    if issue_type is not None:
        conditions.append(Issue.issue_type == issue_type.value)
    if priority is not None:
        conditions.append(Issue.priority == priority.value)
    if assignee_id is not None:
        conditions.append(Issue.assignee_id == assignee_id)
    if unassigned:
        conditions.append(Issue.assignee_id.is_(None))

    base_query = (
        select(Issue)
        .join(Project, Issue.project_id == Project.id)
        .options(contains_eager(Issue.project))
        .where(*conditions)
    )
    total = db.scalar(
        select(func.count(Issue.id))
        .join(Project, Issue.project_id == Project.id)
        .where(*conditions)
    ) or 0
    response.headers["X-Total-Count"] = str(total)
    ordering = Issue.issue_number.asc() if sort == "oldest" else Issue.issue_number.desc()
    issues = db.scalars(
        base_query
        .order_by(ordering)
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
    _ensure_issue_editor(project_member)
    issue = _get_issue(db, project_member.project_id, issue_id)
    changes = issue_update.model_dump(exclude_unset=True)

    for field in ("title", "issue_type", "status", "priority"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )
    if "assignee_id" in changes:
        _ensure_assignee_is_member(db, project_member.project_id, changes["assignee_id"])

    for field, value in changes.items():
        if field == "title" and value is not None:
            value = value.strip()
            if not value:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
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
    issue_id: int, project_member: ProjectAdmin, db: DbSession
) -> Response:
    issue = _get_issue(db, project_member.project_id, issue_id)
    db.delete(issue)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{issue_id}/comments", response_model=list[IssueCommentRead])
def list_issue_comments(
    issue_id: int, project_member: ProjectMemberAccess, db: DbSession
) -> list[IssueCommentRead]:
    _get_issue(db, project_member.project_id, issue_id)
    comments = db.scalars(
        select(IssueComment)
        .where(IssueComment.issue_id == issue_id)
        .order_by(IssueComment.created_at, IssueComment.id)
    ).all()
    return [_comment_read(comment) for comment in comments]


@router.post(
    "/{issue_id}/comments",
    response_model=IssueCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_issue_comment(
    issue_id: int,
    comment_in: IssueCommentCreate,
    project_member: ProjectMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> IssueCommentRead:
    _ensure_issue_editor(project_member)
    _get_issue(db, project_member.project_id, issue_id)
    if comment_in.parent_id is not None:
        parent = db.scalar(
            select(IssueComment).where(
                IssueComment.id == comment_in.parent_id,
                IssueComment.issue_id == issue_id,
            )
        )
        if parent is None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Reply target must be a comment on this issue",
            )
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Replies can only be added to top-level comments",
            )

    comment = IssueComment(
        issue_id=issue_id,
        author_id=current_user.id,
        parent_id=comment_in.parent_id,
        content=comment_in.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_read(comment)
