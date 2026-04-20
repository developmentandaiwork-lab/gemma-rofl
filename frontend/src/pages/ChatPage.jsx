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
      return;
    }
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
    setLoading(true);
    setError("");
    try {
      const result = await api.sendMessage(activeChatId, message);
      setMessages((prev) => [...prev, result.user_message, result.assistant_message]);
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
            <MessageInput disabled={loading} onSend={sendMessage} />
          </>
        ) : (
          <div className="empty">Create or select a chat.</div>
        )}
      </main>
    </div>
  );
}
