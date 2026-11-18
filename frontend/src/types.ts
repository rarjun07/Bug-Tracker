export type Project = {
  id: number;
  name: string;
  key: string;
  description: string | null;
  created_by_id: number;
  created_at: string;
};

export type IssueType = "bug" | "task" | "feature";
export type IssueStatus = "todo" | "in_progress" | "done";
export type IssuePriority = "low" | "medium" | "high" | "urgent";

export type Issue = {
  id: number;
  issue_key: string;
  project_id: number;
  issue_number: number;
  title: string;
  description: string | null;
  issue_type: IssueType;
  status: IssueStatus;
  priority: IssuePriority;
  reporter_id: number;
  assignee_id: number | null;
  created_at: string;
  updated_at: string;
};

export type ProjectMember = {
  user_id: number;
  username: string;
  email: string;
  role: "admin" | "developer" | "viewer";
  joined_at: string;
};

export type NewIssue = {
  title: string;
  description: string;
  issue_type: IssueType;
  priority: IssuePriority;
  assignee_id: number | null;
};
