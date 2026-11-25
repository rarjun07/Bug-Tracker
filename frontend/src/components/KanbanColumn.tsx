import { useDraggable, useDroppable } from "@dnd-kit/react";
import { GripVertical } from "lucide-react";
import type { CSSProperties } from "react";
import type { Issue, IssueStatus, ProjectMember } from "../types";

const statuses: { id: IssueStatus; label: string }[] = [
  { id: "todo", label: "To do" },
  { id: "in_progress", label: "In progress" },
  { id: "done", label: "Done" },
];

type Column = { id: IssueStatus; label: string; color: string };

type Props = {
  column: Column;
  issues: Issue[];
  members: ProjectMember[];
  updatingIds: number[];
  canEdit: boolean;
  onStatusChange: (issueId: number, status: IssueStatus) => Promise<void>;
};

export default function KanbanColumn({ column, issues, members, updatingIds, canEdit, onStatusChange }: Props) {
  const { ref, isDropTarget } = useDroppable({ id: column.id });

  return (
    <section ref={ref} className={`kanban-column ${isDropTarget ? "kanban-column-over" : ""}`} aria-label={`${column.label}: ${issues.length} issues`}>
      <header className="kanban-column-heading">
        <span className={`kanban-column-dot kanban-dot-${column.color}`} />
        <h3>{column.label}</h3>
        <span className="kanban-column-count">{issues.length}</span>
      </header>
      <div className="kanban-card-list">
        {issues.map((issue) => <IssueCard key={issue.id} issue={issue} members={members} updating={updatingIds.includes(issue.id)} canEdit={canEdit} onStatusChange={onStatusChange} />)}
        {issues.length === 0 && <div className="kanban-column-empty">Drop issues here</div>}
      </div>
    </section>
  );
}

function IssueCard({ issue, members, updating, canEdit, onStatusChange }: {
  issue: Issue;
  members: ProjectMember[];
  updating: boolean;
  canEdit: boolean;
  onStatusChange: Props["onStatusChange"];
}) {
  const { ref, handleRef, isDragging } = useDraggable({ id: String(issue.id), disabled: !canEdit });
  const assignee = members.find((member) => member.user_id === issue.assignee_id);

  return (
    <article ref={ref} className={`kanban-card ${isDragging ? "kanban-card-dragging" : ""}`} style={{ "--issue-type-color": typeColor(issue.issue_type) } as CSSProperties}>
      <div className="kanban-card-top">
        <span className="kanban-issue-key">{issue.issue_key}</span>
        {canEdit && <button ref={handleRef} className="kanban-drag-handle" aria-label={`Drag ${issue.issue_key}`} title="Drag issue"><GripVertical size={15} /></button>}
      </div>
      <h4>{issue.title}</h4>
      {issue.description && <p className="kanban-description">{issue.description}</p>}
      <div className="kanban-card-meta">
        <span className={`priority-label priority-${issue.priority}`}><i />{issue.priority}</span>
        {assignee ? <span className="kanban-assignee" title={`Assigned to ${assignee.username}`}><span className="mini-avatar">{assignee.username.slice(0, 1).toUpperCase()}</span>{assignee.username}</span> : <span className="kanban-unassigned">Unassigned</span>}
      </div>
      <label className="kanban-status-label">Status
        {canEdit ? <select aria-label={`Status for ${issue.issue_key}`} value={issue.status} disabled={updating} onChange={(event) => void onStatusChange(issue.id, event.target.value as IssueStatus)}>
          {statuses.map((status) => <option key={status.id} value={status.id}>{status.label}</option>)}
        </select> : <span className={`status-pill status-${issue.status}`}><i />{issue.status.replace("_", " ")}</span>}
      </label>
    </article>
  );
}

function typeColor(type: Issue["issue_type"]) {
  if (type === "bug") return "#dc766e";
  if (type === "feature") return "#9b76c5";
  return "#6173d8";
}
