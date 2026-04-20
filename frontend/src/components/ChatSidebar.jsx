export default function ChatSidebar({ chats, activeChatId, onCreate, onSelect, onDelete }) {
  return (
    <aside className="sidebar">
      <button className="primary" onClick={onCreate}>
        New chat
      </button>
      <div className="chat-list">
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={`chat-item ${chat.id === activeChatId ? "active" : ""}`}
            onClick={() => onSelect(chat.id)}
          >
            <span>{chat.title}</span>
            <button
              className="danger"
              onClick={(event) => {
                event.stopPropagation();
                onDelete(chat.id);
              }}
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
