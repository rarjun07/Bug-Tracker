import { useState, type FormEvent } from "react";
import { Bug, Check, CircleAlert, LoaderCircle, ShieldCheck, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api, { apiErrorMessage } from "../api";

type Props = { onAuthenticated: () => void };

export default function AuthPage({ onAuthenticated }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api.post("/auth/register", { username, email, password });
        setMessage("Your account is ready. Sign in to continue.");
        setMode("login");
        setUsername(email);
      } else {
        const body = new URLSearchParams({ username, password });
        const { data } = await api.post("/auth/token", body, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
        localStorage.setItem("access_token", data.access_token);
        onAuthenticated();
        navigate("/dashboard");
      }
    } catch (submitError) {
      setError(apiErrorMessage(submitError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <div className="brand-lockup">
          <span className="brand-mark"><Bug size={21} strokeWidth={2.4} /></span>
          <span>bugtracker</span>
        </div>
        <div className="story-copy">
          <span className="eyebrow">A calmer way to ship</span>
          <h1>Make room for the work that matters.</h1>
          <p>Bring your team's bugs, ideas, and next steps into one clear place.</p>
          <div className="story-features">
            <div><Check size={16} /><span>Keep every issue moving forward</span></div>
            <div><Users size={16} /><span>Know who's working on what</span></div>
            <div><ShieldCheck size={16} /><span>Your team space stays protected</span></div>
          </div>
        </div>
        <div className="story-footer">A little more clarity, every day.</div>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <span className="auth-mobile-brand"><span className="brand-mark"><Bug size={19} /></span> bugtracker</span>
          <div className="auth-heading">
            <span className="eyebrow">{mode === "login" ? "WELCOME BACK" : "GET STARTED"}</span>
            <h2>{mode === "login" ? "Sign in to your workspace" : "Create your account"}</h2>
            <p>{mode === "login" ? "Your team's work is right where you left it." : "Join your team and start tracking work."}</p>
          </div>

          {message && <div className="notice notice-success"><Check size={16} />{message}</div>}
          {error && <div className="notice notice-error"><CircleAlert size={16} />{error}</div>}

          <form className="form-stack" onSubmit={submit}>
            {mode === "register" && (
              <label className="field">
                <span>Username</span>
                <input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} minLength={3} maxLength={50} required placeholder="e.g. arjun07" />
              </label>
            )}
            {mode === "register" && (
              <label className="field">
                <span>Email</span>
                <input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="you@company.com" />
              </label>
            )}
            {mode === "login" && (
              <label className="field">
                <span>Username or email</span>
                <input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required placeholder="you@company.com" />
              </label>
            )}
            <label className="field">
              <span>Password</span>
              <input type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} maxLength={128} required placeholder="At least 8 characters" />
            </label>
            <button className="button button-primary button-wide" type="submit" disabled={busy}>
              {busy ? <><LoaderCircle className="spin" size={17} /> Please wait…</> : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <p className="auth-switch">
            {mode === "login" ? "New to Bug Tracker?" : "Already have an account?"}{" "}
            <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); setMessage(""); }}>
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>
          <p className="auth-footnote">Your password is protected with secure hashing.</p>
        </div>
      </section>
    </main>
  );
}
