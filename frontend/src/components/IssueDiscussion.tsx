import { useEffect, useState, type FormEvent } from "react";
import { MessageSquare, Send, X } from "lucide-react";
import api, { apiErrorMessage } from "../api";
import type { Issue, IssueComment } from "../types";

export default function IssueDiscussion({ issue, onClose }: { issue: Issue; onClose: () => void }) {
  const [comments, setComments] = useState<IssueComment[]>([]);
  const [content, setContent] = useState("");
  const [replyTo, setReplyTo] = useState<IssueComment | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const endpoint = `/projects/${issue.project_id}/issues/${issue.id}/comments`;

  useEffect(() => {
    let alive = true;
    api.get<IssueComment[]>(endpoint)
      .then(({ data }) => alive && setComments(data))
      .catch((requestError) => alive && setError(apiErrorMessage(requestError)))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [endpoint]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || saving) return;
    setSaving(true);
    setError("");
    try {
      const { data } = await api.post<IssueComment>(endpoint, {
        content: trimmed,
        parent_id: replyTo?.id ?? null,
      });
      setComments((current) => [...current, data]);
      setContent("");
      setReplyTo(null);
    } catch (requestError) {
      setError(apiErrorMessage(requestError));
    } finally {
      setSaving(false);
    }
  }

  const roots = comments.filter((comment) => comment.parent_id === null);

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="issue-modal discussion-modal" role="dialog" aria-modal="true" aria-labelledby="discussion-title">
        <header className="modal-header">
          <div><span className="eyebrow">{issue.issue_key} · TEAM DISCUSSION</span><h2 id="discussion-title">{issue.title}</h2><p>Share updates and reply to your teammates.</p></div>
          <button className="icon-button modal-close" aria-label="Close discussion" onClick={onClose}><X size={18} /></button>
        </header>
        <div className="discussion-list" aria-live="polite">
          {loading ? <div className="loading-state"><span className="loading-spinner" />Loading discussion…</div> : roots.length === 0 ? (
            <div className="discussion-empty"><MessageSquare size={19} /><strong>No comments yet</strong><span>Start a conversation about this issue.</span></div>
          ) : roots.map((comment) => (
            <article className="comment-thread" key={comment.id}>
              <CommentBubble comment={comment} />
              {comments.filter((reply) => reply.parent_id === comment.id).map((reply) => <CommentBubble comment={reply} key={reply.id} reply />)}
              <button className="comment-reply-button" onClick={() => { setReplyTo(comment); setContent(""); }}>Reply</button>
            </article>
          ))}
        </div>
        {error && <div className="notice notice-error modal-notice" role="alert">{error}</div>}
        <form className="comment-composer" onSubmit={submit}>
          {replyTo && <div className="reply-context"><span>Replying to {replyTo.author_username}</span><button type="button" onClick={() => setReplyTo(null)} aria-label="Cancel reply"><X size={14} /></button></div>}
          <label className="sr-only" htmlFor="comment-content">Write a comment</label>
          <textarea id="comment-content" value={content} maxLength={5000} rows={3} placeholder={replyTo ? "Write a reply…" : "Write a comment…"} onChange={(event) => setContent(event.target.value)} />
          <div className="comment-composer-footer"><span>{content.length}/5000</span><button className="button button-primary" disabled={!content.trim() || saving || loading}>{saving ? "Sending…" : <><Send size={14} /> Send {replyTo ? "reply" : "comment"}</>}</button></div>
        </form>
      </section>
    </div>
  );
}

function CommentBubble({ comment, reply = false }: { comment: IssueComment; reply?: boolean }) {
  const date = new Date(comment.created_at);
  return (
    <div className={`comment-bubble ${reply ? "comment-reply" : ""}`}>
      <div className="comment-avatar">{comment.author_username.slice(0, 1).toUpperCase()}</div>
      <div className="comment-body">
        <div className="comment-meta"><strong>{comment.author_username}</strong><time dateTime={comment.created_at}>{Number.isNaN(date.getTime()) ? "Just now" : date.toLocaleString()}</time></div>
        <p>{comment.content}</p>
      </div>
    </div>
  );
}
