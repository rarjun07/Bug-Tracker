import { useEffect, useMemo, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  ArrowDownUp,
  Bug,
  CheckCircle2,
  ChevronDown,
  CircleDashed,
  CirclePlus,
  ClipboardList,
  FolderKanban,
  LogOut,
  Menu,
  MessageSquare,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import api, { apiErrorMessage } from "../api";
import type { Issue, Project, ProjectMember } from "../types";
import DashboardOverview from "./DashboardOverview";
import IssueForm from "./IssueForm";
import KanbanBoard from "./KanbanBoard";
import IssueDiscussion from "./IssueDiscussion";

type Props = { view: "dashboard" | "issues" | "kanban"; onLogout: () => void };

export default function IssueBoard({ view, onLogout }: Props) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | null>(() => Number(localStorage.getItem("active_project_id")) || null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingIssues, setLoadingIssues] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [discussionIssue, setDiscussionIssue] = useState<Issue | null>(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const activeProject = projects.find((project) => project.id === projectId) ?? null;

  useEffect(() => {
    let alive = true;
    api.get<Project[]>("/projects")
      .then(({ data }) => {
        if (!alive) return;
        setProjects(data);
        const savedId = Number(localStorage.getItem("active_project_id"));
        const selectedId = data.some((project) => project.id === savedId) ? savedId : data[0]?.id ?? null;
        setProjectId(selectedId);
        if (selectedId === null) localStorage.removeItem("active_project_id");
        else localStorage.setItem("active_project_id", String(selectedId));
      })
      .catch((requestError) => {
        if (alive) setError(apiErrorMessage(requestError));
      })
      .finally(() => alive && setLoadingProjects(false));
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (projectId === null) {
      setIssues([]);
      setMembers([]);
      return;
    }
    let alive = true;
    setLoadingIssues(true);
    setError("");
    Promise.all([
      api.get<Issue[]>(`/projects/${projectId}/issues`),
      api.get<ProjectMember[]>(`/projects/${projectId}/members`),
    ])
      .then(([issueResponse, memberResponse]) => {
        if (!alive) return;
        setIssues(issueResponse.data);
        setMembers(memberResponse.data);
      })
      .catch((requestError) => {
        if (alive) setError(apiErrorMessage(requestError));
      })
      .finally(() => alive && setLoadingIssues(false));
    return () => { alive = false; };
  }, [projectId]);

  const visibleIssues = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return issues;
    return issues.filter((issue) => `${issue.issue_key} ${issue.title} ${issue.description ?? ""}`.toLowerCase().includes(term));
  }, [issues, search]);
  const inProgressCount = issues.filter((issue) => issue.status === "in_progress").length;
  const doneCount = issues.filter((issue) => issue.status === "done").length;

  function logout() {
    localStorage.removeItem("access_token");
    onLogout();
    navigate("/login");
  }

  function addIssue(issue: Issue) {
    setIssues((existing) => [issue, ...existing]);
    setShowForm(false);
  }

  async function updateIssueStatus(issueId: number, status: Issue["status"]) {
    const previous = issues.find((issue) => issue.id === issueId);
    if (!previous || previous.status === status) return;
    setIssues((existing) => existing.map((issue) => issue.id === issueId ? { ...issue, status } : issue));
    try {
      await api.patch(`/projects/${previous.project_id}/issues/${issueId}`, { status });
    } catch (requestError) {
      setIssues((existing) => existing.map((issue) => issue.id === issueId && issue.status === status ? { ...issue, status: previous.status } : issue));
      throw requestError;
    }
  }

  return (
    <div className="workspace-shell">
      {sidebarOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand-lockup sidebar-brand">
          <span className="brand-mark"><Bug size={20} strokeWidth={2.4} /></span>
          <span>bugtracker</span>
        </div>
        <div className="workspace-switcher">
          <span className="workspace-avatar">{activeProject?.key.slice(0, 2) ?? "BT"}</span>
          <label className="workspace-select-wrap">
            <span className="workspace-label">WORKSPACE</span>
            <select aria-label="Choose project" value={projectId ?? ""} onChange={(event) => {
              const selectedId = Number(event.target.value) || null;
              setProjectId(selectedId);
              if (selectedId === null) localStorage.removeItem("active_project_id");
              else localStorage.setItem("active_project_id", String(selectedId));
            }} disabled={!projects.length}>
              {projects.length === 0 ? <option value="">No project yet</option> : projects.map((project) => <option value={project.id} key={project.id}>{project.name}</option>)}
            </select>
            <ChevronDown className="select-chevron" size={14} />
          </label>
        </div>
        <div className="nav-section-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          <NavLink onClick={() => setSidebarOpen(false)} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`} to="/dashboard"><FolderKanban size={17} /><span>Dashboard</span></NavLink>
          <NavLink onClick={() => setSidebarOpen(false)} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`} to="/issues"><ClipboardList size={17} /><span>Issues</span><span className="nav-count">{issues.length}</span></NavLink>
          <NavLink onClick={() => setSidebarOpen(false)} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`} to="/kanban"><FolderKanban size={17} /><span>Kanban</span></NavLink>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-tip"><Sparkles size={16} /><span>Keep your team's next step in sight.</span></div>
          <button className="profile-button" onClick={logout}>
            <span className="profile-avatar">U</span>
            <span className="profile-meta"><strong>Your account</strong><small>Signed in</small></span>
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main className="workspace-main">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setSidebarOpen(true)}><Menu size={19} /></button>
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-separator">/</span><strong>{activeProject?.name ?? "Issues"}</strong></div>
          <div className="topbar-actions"><span className="sync-indicator"><span /> Connected</span><button className="top-logout" onClick={logout} aria-label="Sign out"><LogOut size={17} /></button></div>
        </header>

        <div className="page-content">
          <div className="page-heading-row">
            <div>
              <div className="eyebrow page-eyebrow">PROJECT TRACKER <span className="heading-dot">•</span> {activeProject?.key ?? "YOUR WORKSPACE"}</div>
              <h1>{view === "dashboard" ? "Project dashboard" : view === "kanban" ? "Kanban board" : "Issues"} <span className="heading-count">{issues.length}</span></h1>
              <p className="page-subtitle">{view === "dashboard" ? "A clear view of your team's work and what's next." : view === "kanban" ? "See every issue and move work through the project." : "Keep the details clear and the work moving."}</p>
            </div>
            <button className="button button-primary create-button" disabled={!activeProject} onClick={() => setShowForm(true)}><CirclePlus size={17} /> New issue</button>
          </div>

          <div className="summary-grid">
            <div className="summary-card"><span className="summary-icon summary-icon-blue"><ClipboardList size={17} /></span><div><span>Total issues</span><strong>{issues.length}</strong></div><span className="summary-caption">in this project</span></div>
            <div className="summary-card"><span className="summary-icon summary-icon-amber"><CircleDashed size={17} /></span><div><span>In progress</span><strong>{inProgressCount}</strong></div><span className="summary-caption">currently active</span></div>
            <div className="summary-card"><span className="summary-icon summary-icon-green"><CheckCircle2 size={17} /></span><div><span>Completed</span><strong>{doneCount}</strong></div><span className="summary-caption">across the team</span></div>
          </div>

          {error && <div className="notice notice-error page-notice"><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><X size={16} /></button></div>}

          {view === "dashboard" && activeProject && !loadingProjects && !loadingIssues ? (
            <DashboardOverview project={activeProject} issues={issues} members={members} />
          ) : view === "dashboard" && loadingProjects ? (
            <section className="issues-panel"><div className="loading-state"><span className="loading-spinner" />Loading your dashboard…</div></section>
          ) : view === "dashboard" && !projects.length ? (
            <section className="issues-panel"><div className="empty-state"><span className="empty-icon"><FolderKanban size={22} /></span><h3>Create your first project</h3><p>Projects organize issues and teams. Create one from the API docs, then come back here.</p><a className="button button-secondary" href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/docs`} target="_blank" rel="noreferrer">Open API docs</a></div></section>
          ) : view === "dashboard" ? (
            <section className="issues-panel"><div className="loading-state"><span className="loading-spinner" />Loading project details…</div></section>
          ) : view === "kanban" ? (
            <KanbanBoard issues={visibleIssues} members={members} loading={loadingProjects || loadingIssues} onStatusChange={updateIssueStatus} onCreateIssue={() => setShowForm(true)} />
          ) : <section className="issues-panel">
            <div className="panel-header">
              <div><h2>All issues</h2><p>{activeProject ? `Issues in ${activeProject.name}` : "Choose a project to get started"}</p></div>
              <div className="panel-tools">
                <label className="search-box"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search issues" aria-label="Search issues" /></label>
                <button className="sort-button" title="Sorted by newest"><ArrowDownUp size={15} /><span>Newest</span></button>
              </div>
            </div>

            {loadingProjects || loadingIssues ? (
              <div className="loading-state"><span className="loading-spinner" />Loading your issues…</div>
            ) : !projects.length ? (
              <div className="empty-state">
                <span className="empty-icon"><FolderKanban size={22} /></span>
                <h3>Create your first project</h3>
                <p>Projects organize issues and teams. Create one from the API docs, then come back here.</p>
                <a className="button button-secondary" href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/docs`} target="_blank" rel="noreferrer">Open API docs</a>
              </div>
            ) : !visibleIssues.length ? (
              <div className="empty-state">
                <span className="empty-icon"><ClipboardList size={22} /></span>
                <h3>{search ? "No matching issues" : "A clean slate"}</h3>
                <p>{search ? "Try a different search term." : "Create the first issue for this project and give the work a clear starting point."}</p>
                {!search && <button className="button button-secondary" onClick={() => setShowForm(true)}><CirclePlus size={16} /> Create first issue</button>}
              </div>
            ) : (
              <div className="issue-table-wrap">
                <table className="issue-table">
                  <thead><tr><th>Issue</th><th>Type</th><th>Status</th><th>Priority</th><th>Assignee</th><th>Discussion</th></tr></thead>
                  <tbody>{visibleIssues.map((issue) => {
                    const assignee = members.find((member) => member.user_id === issue.assignee_id);
                    return <tr key={issue.id}>
                      <td><div className="issue-title-cell"><span className={`issue-type-mark type-${issue.issue_type}`}><Bug size={14} /></span><span><strong>{issue.title}</strong><small>{issue.issue_key}{issue.description ? ` · ${issue.description}` : ""}</small></span></div></td>
                      <td><span className="type-label">{issue.issue_type}</span></td>
                      <td><span className={`status-pill status-${issue.status}`}><i />{issue.status.replace("_", " ")}</span></td>
                      <td><span className={`priority-label priority-${issue.priority}`}><i />{issue.priority}</span></td>
                      <td>{assignee ? <span className="assignee-cell"><span className="mini-avatar">{assignee.username.slice(0, 1).toUpperCase()}</span>{assignee.username}</span> : <span className="unassigned">Unassigned</span>}</td>
                      <td><button className="discussion-open-button" onClick={() => setDiscussionIssue(issue)}><MessageSquare size={14} /> Open</button></td>
                    </tr>;
                  })}</tbody>
                </table>
              </div>
            )}
            {visibleIssues.length > 0 && <div className="panel-footer"><span>Showing {visibleIssues.length} of {issues.length} issues</span><span className="footer-project"><span className="footer-project-dot" /> {activeProject?.key}</span></div>}
          </section>}
          <footer className="page-footer"><span>Built for thoughtful teamwork.</span><span>Bug Tracker <span className="footer-divider">·</span> Day 9</span></footer>
        </div>
      </main>

      {showForm && activeProject && <IssueForm project={activeProject} members={members} onClose={() => setShowForm(false)} onCreated={addIssue} />}
      {discussionIssue && <IssueDiscussion issue={discussionIssue} onClose={() => setDiscussionIssue(null)} />}
    </div>
  );
}
