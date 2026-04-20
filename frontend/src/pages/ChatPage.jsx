import { useEffect, useState } from "react";
import { api } from "../api";
import ChatSidebar from "../components/ChatSidebar";
import MessageList from "../components/MessageList";
import MessageInput from "../components/MessageInput";

export default function ChatPage({ user, onLogout }) {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pendingJob, setPendingJob] = useState(null);
  const [pendingStartedAt, setPendingStartedAt] = useState(null);
  const [pendingElapsed, setPendingElapsed] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState("");

  const loadChats = async () => {
    const data = await api.listChats();
    setChats(data);
    if (!activeChatId && data.length > 0) {
      setActiveChatId(data[0].id);
    }
  };

  useEffect(() => {
    loadChats().catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!activeChatId) {
      setMessages([]);
      setPendingJob(null);
      return;
    }
    setPendingJob(null);
    api
      .listMessages(activeChatId)
      .then(setMessages)
      .catch((err) => setError(err.message));
  }, [activeChatId]);

  const createChat = async () => {
    try {
      const chat = await api.createChat({});
      await loadChats();
      setActiveChatId(chat.id);
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteChat = async (chatId) => {
    if (!window.confirm("Delete this chat?")) return;
    try {
      await api.deleteChat(chatId);
      const next = chats.filter((chat) => chat.id !== chatId);
      setChats(next);
      setActiveChatId(next[0]?.id || null);
    } catch (err) {
      setError(err.message);
    }
  };

  const sendMessage = async (message) => {
    if (!activeChatId) return;
    if (pendingJob) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.sendMessage(activeChatId, message);
      setMessages((prev) => [...prev, result.user_message]);
      setPendingJob({ jobId: result.job_id, chatId: activeChatId });
      setPendingStartedAt(Date.now());
      await loadChats();
    } catch (err) {
      if (err.status === 401) {
        onLogout();
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!pendingJob) return;
    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const status = await api.getJobStatus(pendingJob.chatId, pendingJob.jobId);
        if (cancelled) return;
        if (status.status === "completed" && status.assistant_message) {
          setMessages((prev) => {
            if (prev.some((m) => m.id === status.assistant_message.id)) return prev;
            return [...prev, status.assistant_message];
          });
          setPendingJob(null);
          setPendingStartedAt(null);
          setPendingElapsed(0);
          await loadChats();
        } else if (status.status === "failed") {
          setError(status.error || "Assistant request failed");
          setPendingJob(null);
          setPendingStartedAt(null);
          setPendingElapsed(0);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setPendingJob(null);
          setPendingStartedAt(null);
          setPendingElapsed(0);
        }
      }
    }, 1500);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [pendingJob]);

  useEffect(() => {
    if (!pendingStartedAt) return;
    const timer = setInterval(() => {
      setPendingElapsed(Math.floor((Date.now() - pendingStartedAt) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [pendingStartedAt]);

  const formattedPending = `${String(Math.floor(pendingElapsed / 60)).padStart(2, "0")}:${String(
    pendingElapsed % 60
  ).padStart(2, "0")}`;

  return (
    <div className="chat-shell">
      <header className="app-header">PENSILGPT</header>
      <div className="chat-layout">
      {sidebarOpen ? <button className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} aria-label="Close menu" /> : null}
      <ChatSidebar
        chats={chats}
        activeChatId={activeChatId}
        onCreate={createChat}
        onSelect={setActiveChatId}
        onDelete={deleteChat}
        onClose={() => setSidebarOpen(false)}
        className={sidebarOpen ? "open" : ""}
      />
      <main className="chat-main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setSidebarOpen((prev) => !prev)} aria-label="Toggle chats">
            ☰
          </button>
          <div>{user.email}</div>
          <button onClick={onLogout}>Logout</button>
        </header>
        {error ? <p className="error">{error}</p> : null}
        {activeChatId ? (
          <>
            <MessageList messages={messages} />
            {pendingJob ? (
              <div className="cat-loader-wrap" role="status" aria-live="polite">
                <div className="pending-timer">Response time: {formattedPending}</div>
                <div className="cat-loader" aria-label="Loading assistant response">
                  🐱
                </div>
              </div>
            ) : null}
            <MessageInput disabled={loading} onSend={sendMessage} />
          </>
        ) : (
          <div className="empty">Create or select a chat.</div>
        )}
      </main>
    </div>
    </div>
  );
}
