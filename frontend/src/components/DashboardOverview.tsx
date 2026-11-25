import { ArrowRight, CircleDashed, Clock3, Flag, Users } from "lucide-react";
import { Link } from "react-router-dom";
import type { Issue, IssuePriority, IssueStatus, Project, ProjectMember } from "../types";

type Props = {
  project: Project;
  issues: Issue[];
  members: ProjectMember[];
  totalIssues: number;
};

const statusLabels: Record<IssueStatus, string> = {
  todo: "To do",
  in_progress: "In progress",
  done: "Done",
};

const priorityLabels: Record<IssuePriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  urgent: "Urgent",
};

export default function DashboardOverview({ project, issues, members, totalIssues }: Props) {
  const statuses: IssueStatus[] = ["todo", "in_progress", "done"];
  const priorities: IssuePriority[] = ["urgent", "high", "medium", "low"];
  const statusCounts = Object.fromEntries(
    statuses.map((status) => [status, issues.filter((issue) => issue.status === status).length]),
  ) as Record<IssueStatus, number>;
  const priorityCounts = Object.fromEntries(
    priorities.map((priority) => [priority, issues.filter((issue) => issue.priority === priority).length]),
  ) as Record<IssuePriority, number>;
  const recentIssues = [...issues].sort((a, b) => b.issue_number - a.issue_number).slice(0, 5);
  const isSample = totalIssues > issues.length;

  return (
    <div className="dashboard-grid">
      <section className="dashboard-card status-card">
        <div className="dashboard-card-heading">
          <span className="dashboard-heading-icon icon-violet"><CircleDashed size={17} /></span>
          <div><h2>Issue status</h2><p>{isSample ? `Based on the latest ${issues.length} issues` : "How work is moving across the project"}</p></div>
        </div>
        <div className="status-breakdown">
          {statuses.map((status) => {
            const count = statusCounts[status];
            const percent = issues.length ? Math.round((count / issues.length) * 100) : 0;
            return (
              <div className="status-breakdown-row" key={status}>
                <div className="status-breakdown-label"><span className={`status-dot status-dot-${status}`} />{statusLabels[status]}<strong>{count}</strong></div>
                <div className="status-track" role="img" aria-label={`${statusLabels[status]}: ${count} issues`}>
                  <span className={`status-fill status-fill-${status}`} style={{ width: `${percent}%` }} />
                </div>
              </div>
            );
          })}
        </div>
        <div className="dashboard-card-foot"><span>{isSample ? `Showing ${issues.length} of ${totalIssues} issues` : `${totalIssues} issue${totalIssues === 1 ? "" : "s"} total`}</span><Link to="/issues">View issue list <ArrowRight size={13} /></Link></div>
      </section>

      <section className="dashboard-card priority-card">
        <div className="dashboard-card-heading">
          <span className="dashboard-heading-icon icon-amber"><Flag size={16} /></span>
          <div><h2>Priority overview</h2><p>{isSample ? `Latest ${issues.length} issues` : "Where attention is needed first"}</p></div>
        </div>
        <div className="priority-breakdown">
          {priorities.map((priority) => (
            <div className="priority-breakdown-row" key={priority}>
              <span className={`priority-label priority-${priority}`}><i />{priorityLabels[priority]}</span>
              <span className="priority-track"><span className={`priority-bar priority-bar-${priority}`} style={{ width: `${priorityCounts[priority] ? Math.max(5, (priorityCounts[priority] / issues.length) * 100) : 0}%` }} /></span>
              <strong>{priorityCounts[priority]}</strong>
            </div>
          ))}
        </div>
        <div className="dashboard-card-foot"><span>{isSample ? "Urgent/high in this sample" : "Urgent and high priority"}</span><strong>{priorityCounts.urgent + priorityCounts.high}</strong></div>
      </section>

      <section className="dashboard-card recent-card">
        <div className="dashboard-card-heading">
          <span className="dashboard-heading-icon icon-blue"><Clock3 size={16} /></span>
          <div><h2>Recently created</h2><p>The latest issues added to {project.key}</p></div>
          <Link className="card-heading-link" to="/issues" aria-label="View all issues"><ArrowRight size={16} /></Link>
        </div>
        {recentIssues.length ? (
          <div className="recent-list">
            {recentIssues.map((issue) => (
              <div className="recent-row" key={issue.id}>
                <span className={`recent-type recent-type-${issue.issue_type}`} />
                <div className="recent-main"><strong>{issue.title}</strong><small>{issue.issue_key} <span>·</span> {issue.issue_type}</small></div>
                <span className={`status-pill status-${issue.status}`}><i />{statusLabels[issue.status]}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="dashboard-empty"><p>No issues yet. Create the first one to get work moving.</p><Link to="/issues">Open issue list <ArrowRight size={13} /></Link></div>
        )}
      </section>

      <section className="dashboard-card team-card">
        <div className="dashboard-card-heading">
          <span className="dashboard-heading-icon icon-green"><Users size={16} /></span>
          <div><h2>Project team</h2><p>People working in {project.name}</p></div>
        </div>
        <div className="team-list">
          {members.slice(0, 5).map((member) => (
            <div className="team-row" key={member.user_id}>
              <span className={`team-avatar team-avatar-${member.role}`}>{member.username.slice(0, 1).toUpperCase()}</span>
              <span className="team-person"><strong>{member.username}</strong><small>{member.email}</small></span>
              <span className={`role-label role-${member.role}`}>{member.role}</span>
            </div>
          ))}
          {!members.length && <p className="team-empty">Team details will appear here.</p>}
        </div>
        <div className="dashboard-card-foot"><span>{members.length} team member{members.length === 1 ? "" : "s"}</span><span className="team-project-tag">{project.key}</span></div>
      </section>
    </div>
  );
}
