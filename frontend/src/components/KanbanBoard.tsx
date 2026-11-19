import { DragDropProvider } from "@dnd-kit/react";
import { Bug, GripVertical } from "lucide-react";
import { useState } from "react";
import type { Issue, IssueStatus, ProjectMember } from "../types";
import { apiErrorMessage } from "../api";
import KanbanColumn from "./KanbanColumn";

const columns: { id: IssueStatus; label: string; color: string }[] = [
  { id: "todo", label: "To do", color: "todo" },
  { id: "in_progress", label: "In progress", color: "progress" },
  { id: "done", label: "Done", color: "done" },
];

type Props = {
  issues: Issue[];
  members: ProjectMember[];
  loading: boolean;
  onStatusChange: (issueId: number, status: IssueStatus) => Promise<void>;
  onCreateIssue: () => void;
};

export default function KanbanBoard({ issues, members, loading, onStatusChange, onCreateIssue }: Props) {
  const [updatingIds, setUpdatingIds] = useState<number[]>([]);
  const [error, setError] = useState("");

  async function changeStatus(issueId: number, status: IssueStatus) {
    const issue = issues.find((item) => item.id === issueId);
    if (!issue || issue.status === status || updatingIds.includes(issueId)) return;
    setUpdatingIds((current) => [...current, issueId]);
    setError("");
    try {
      await onStatusChange(issueId, status);
    } catch (requestError) {
      setError(apiErrorMessage(requestError));
    } finally {
      setUpdatingIds((current) => current.filter((id) => id !== issueId));
    }
  }

  return (
    <DragDropProvider onDragEnd={(event) => {
      if (event.canceled) return;
      const sourceId = event.operation.source?.id;
      const targetId = event.operation.target?.id;
      const status = columns.find((column) => column.id === targetId)?.id;
      const issueId = Number(sourceId);
      if (status && Number.isInteger(issueId)) void changeStatus(issueId, status);
    }}>
      <section className="kanban-panel" aria-label="Issue board">
        <div className="kanban-header">
          <div><h2>Kanban board</h2><p>Drag an issue to update its status, or use the status menu on a card.</p></div>
          <button className="button button-secondary kanban-create" onClick={onCreateIssue}>+ New issue</button>
        </div>
        {error && <div className="notice notice-error kanban-notice" role="alert">{error}</div>}
        {loading ? <div className="loading-state"><span className="loading-spinner" />Loading issues…</div> : (
          <div className="kanban-columns">
            {columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                issues={issues.filter((issue) => issue.status === column.id)}
                members={members}
                updatingIds={updatingIds}
                onStatusChange={changeStatus}
              />
            ))}
          </div>
        )}
        {!loading && issues.length === 0 && <div className="kanban-empty"><Bug size={18} /><span>No issues yet. Create one to start the board.</span></div>}
        <div className="kanban-hint"><GripVertical size={14} /> Drag cards between columns to update issue status.</div>
      </section>
    </DragDropProvider>
  );
}
