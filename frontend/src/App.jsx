import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ChatPage from "./pages/ChatPage";

function ProtectedRoute({ user, children }) {
  if (!getToken()) {
    return <Navigate to="/login" replace />;
  }
  if (!user) {
    return <div className="centered">Loading...</div>;
  }
  return children;
}

export default function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(Boolean(getToken()));

  useEffect(() => {
    async function loadUser() {
      if (!getToken()) {
        setLoadingUser(false);
        return;
      }
      try {
        const me = await api.me();
        setUser(me);
      } catch {
        setToken(null);
        setUser(null);
      } finally {
        setLoadingUser(false);
      }
    }
    loadUser();
  }, []);

  const onAuthSuccess = async (token) => {
    setToken(token);
    const me = await api.me();
    setUser(me);
    navigate("/chat");
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    navigate("/login");
  };

  if (loadingUser) {
    return <div className="centered">Loading...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage onAuthSuccess={onAuthSuccess} />} />
      <Route path="/register" element={<RegisterPage onAuthSuccess={onAuthSuccess} />} />
      <Route
        path="/chat"
        element={
          <ProtectedRoute user={user}>
            <ChatPage user={user} onLogout={logout} />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to={getToken() ? "/chat" : "/login"} replace />} />
    </Routes>
  );
}
