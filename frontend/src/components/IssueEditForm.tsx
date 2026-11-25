import { useState, type FormEvent } from "react";
import { CircleAlert, LoaderCircle, X } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import type { Issue, IssuePriority, IssueStatus, IssueType, Project, ProjectMember } from "../types";

type Props = {
  issue: Issue;
  project: Project;
  members: ProjectMember[];
  onClose: () => void;
  onUpdated: (issue: Issue) => void;
};

export default function IssueEditForm({ issue, project, members, onClose, onUpdated }: Props) {
  const [title, setTitle] = useState(issue.title);
  const [description, setDescription] = useState(issue.description ?? "");
  const [issueType, setIssueType] = useState<IssueType>(issue.issue_type);
  const [status, setStatus] = useState<IssueStatus>(issue.status);
  const [priority, setPriority] = useState<IssuePriority>(issue.priority);
  const [assigneeId, setAssigneeId] = useState(issue.assignee_id?.toString() ?? "");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle || busy) return;
    setError("");
    setBusy(true);
    try {
      const { data } = await api.patch<Issue>(`/projects/${project.id}/issues/${issue.id}`, {
        title: trimmedTitle,
        description: description.trim() || null,
        issue_type: issueType,
        status,
        priority,
        assignee_id: assigneeId ? Number(assigneeId) : null,
      });
      onUpdated(data);
    } catch (requestError) {
      setError(apiErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onClose(); }}>
      <section className="issue-modal" role="dialog" aria-modal="true" aria-labelledby="edit-issue-title">
        <header className="modal-header">
          <div><span className="eyebrow">{issue.issue_key} · EDIT ISSUE</span><h2 id="edit-issue-title">Update issue</h2><p>Changes are shared with everyone in {project.name}.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close" disabled={busy}><X size={19} /></button>
        </header>
        {error && <div className="notice notice-error modal-notice" role="alert"><CircleAlert size={16} />{error}</div>}
        <form onSubmit={submit} className="issue-form">
          <label className="field"><span>Issue title <b>*</b></span><input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} required /></label>
          <label className="field"><span>Description <em>Optional</em></span><textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={20000} rows={4} /></label>
          <div className="form-row">
            <label className="field"><span>Issue type</span><select value={issueType} onChange={(event) => setIssueType(event.target.value as IssueType)}><option value="bug">Bug</option><option value="task">Task</option><option value="feature">Feature request</option></select></label>
            <label className="field"><span>Status</span><select value={status} onChange={(event) => setStatus(event.target.value as IssueStatus)}><option value="todo">To do</option><option value="in_progress">In progress</option><option value="done">Done</option></select></label>
          </div>
          <div className="form-row">
            <label className="field"><span>Priority</span><select value={priority} onChange={(event) => setPriority(event.target.value as IssuePriority)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label>
            <label className="field"><span>Assignee <em>Optional</em></span><select value={assigneeId} onChange={(event) => setAssigneeId(event.target.value)}><option value="">Unassigned</option>{members.map((member) => <option value={member.user_id} key={member.user_id}>{member.username} · {member.role}</option>)}</select></label>
          </div>
          <div className="modal-actions"><button type="button" className="button button-secondary" onClick={onClose} disabled={busy}>Cancel</button><button type="submit" className="button button-primary" disabled={busy || !title.trim()}>{busy ? <><LoaderCircle className="spin" size={16} /> Saving…</> : "Save changes"}</button></div>
        </form>
      </section>
    </div>
  );
}
