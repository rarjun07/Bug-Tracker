import { useState, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AuthPage from "./components/AuthPage";
import IssueBoard from "./components/IssueBoard";

function Protected({ children }: { children: ReactNode }) {
  return localStorage.getItem("access_token") ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  const [, setSessionVersion] = useState(0);
  const refreshSession = () => setSessionVersion((version) => version + 1);

  return (
    <Routes>
      <Route path="/login" element={<AuthPage onAuthenticated={refreshSession} />} />
      <Route
        path="/issues"
        element={
          <Protected>
            <IssueBoard onLogout={refreshSession} />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to={localStorage.getItem("access_token") ? "/issues" : "/login"} replace />} />
    </Routes>
  );
}
