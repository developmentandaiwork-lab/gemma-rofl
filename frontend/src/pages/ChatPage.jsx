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
          await loadChats();
        } else if (status.status === "failed") {
          setError(status.error || "Assistant request failed");
          setPendingJob(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setPendingJob(null);
        }
      }
    }, 1500);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [pendingJob]);

  return (
    <div className="chat-layout">
      <ChatSidebar
        chats={chats}
        activeChatId={activeChatId}
        onCreate={createChat}
        onSelect={setActiveChatId}
        onDelete={deleteChat}
      />
      <main className="chat-main">
        <header className="topbar">
          <div>{user.email}</div>
          <button onClick={onLogout}>Logout</button>
        </header>
        {error ? <p className="error">{error}</p> : null}
        {activeChatId ? (
          <>
            <MessageList messages={messages} />
            {pendingJob ? (
              <div className="cat-loader-wrap">
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
  );
}
