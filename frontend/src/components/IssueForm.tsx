import { useState, type FormEvent } from "react";
import { CircleAlert, LoaderCircle, X } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import type { Issue, IssuePriority, IssueType, NewIssue, Project, ProjectMember } from "../types";

type Props = {
  project: Project;
  members: ProjectMember[];
  onClose: () => void;
  onCreated: (issue: Issue) => void;
};

export default function IssueForm({ project, members, onClose, onCreated }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [issueType, setIssueType] = useState<IssueType>("bug");
  const [priority, setPriority] = useState<IssuePriority>("medium");
  const [assigneeId, setAssigneeId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const payload: NewIssue = {
      title: title.trim(),
      description: description.trim(),
      issue_type: issueType,
      priority,
      assignee_id: assigneeId ? Number(assigneeId) : null,
    };
    try {
      const { data } = await api.post<Issue>(`/projects/${project.id}/issues`, payload);
      onCreated(data);
    } catch (submitError) {
      setError(apiErrorMessage(submitError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="issue-modal" role="dialog" aria-modal="true" aria-labelledby="issue-modal-title">
        <header className="modal-header">
          <div><span className="eyebrow">{project.key} · NEW ISSUE</span><h2 id="issue-modal-title">Create an issue</h2><p>Capture the details so your team can take it from here.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close"><X size={19} /></button>
        </header>
        {error && <div className="notice notice-error modal-notice"><CircleAlert size={16} />{error}</div>}
        <form onSubmit={submit} className="issue-form">
          <label className="field"><span>Issue title <b>*</b></span><input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} required placeholder="What needs attention?" /></label>
          <label className="field"><span>Description <em>Optional</em></span><textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={20000} rows={4} placeholder="Add context, steps to reproduce, or what success looks like…" /></label>
          <div className="form-row">
            <label className="field"><span>Issue type</span><select value={issueType} onChange={(event) => setIssueType(event.target.value as IssueType)}><option value="bug">Bug</option><option value="task">Task</option><option value="feature">Feature request</option></select></label>
            <label className="field"><span>Priority</span><select value={priority} onChange={(event) => setPriority(event.target.value as IssuePriority)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="urgent">Urgent</option></select></label>
          </div>
          <label className="field"><span>Assignee <em>Optional</em></span><select value={assigneeId} onChange={(event) => setAssigneeId(event.target.value)}><option value="">Leave unassigned</option>{members.map((member) => <option value={member.user_id} key={member.user_id}>{member.username} · {member.role}</option>)}</select></label>
          <div className="modal-actions"><button type="button" className="button button-secondary" onClick={onClose} disabled={busy}>Cancel</button><button type="submit" className="button button-primary" disabled={busy || !title.trim()}>{busy ? <><LoaderCircle className="spin" size={16} /> Creating…</> : "Create issue"}</button></div>
        </form>
      </section>
    </div>
  );
}
