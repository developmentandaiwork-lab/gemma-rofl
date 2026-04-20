import { useEffect, useRef } from "react";

export default function MessageList({ messages }) {
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="messages" ref={listRef}>
      {messages.length === 0 ? (
        <div className="empty">No messages yet.</div>
      ) : (
        messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
            <p>{message.content}</p>
          </div>
        ))
      )}
    </div>
  );
}
