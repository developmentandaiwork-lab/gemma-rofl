import { useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MessageList({ messages, activeChatId }) {
  const listRef = useRef(null);
  const [copiedKey, setCopiedKey] = useState(null);

  const handleCopy = async (text, key) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey((prev) => (prev === key ? null : prev)), 1200);
    } catch {
      setCopiedKey(null);
    }
  };

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (!listRef.current) return;
    requestAnimationFrame(() => {
      if (!listRef.current) return;
      listRef.current.scrollTop = listRef.current.scrollHeight;
      setTimeout(() => {
        if (listRef.current) {
          listRef.current.scrollTop = listRef.current.scrollHeight;
        }
      }, 120);
    });
  }, [activeChatId]);

  return (
    <div className="messages" ref={listRef}>
      {messages.length === 0 ? (
        <div className="empty">No messages yet.</div>
      ) : (
        messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-head">
              <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
              {message.role === "assistant" ? (
                <button
                  type="button"
                  className="copy-btn ghost-btn"
                  onClick={() => handleCopy(message.content, `message-${message.id}`)}
                >
                  {copiedKey === `message-${message.id}` ? "Copied" : "Copy"}
                </button>
              ) : null}
            </div>
            {message.role === "assistant" ? (
              <div className="markdown-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ inline, className, children, ...props }) {
                      const codeContent = String(children).replace(/\n$/, "");
                      if (inline) {
                        return (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      }
                      const codeKey = `code-${message.id}-${codeContent.slice(0, 30)}`;
                      return (
                        <div className="code-block-wrap">
                          <button
                            type="button"
                            className="copy-btn code-copy-btn"
                            onClick={() => handleCopy(codeContent, codeKey)}
                          >
                            {copiedKey === codeKey ? "Copied" : "Copy code"}
                          </button>
                          <pre>
                            <code className={className} {...props}>
                              {codeContent}
                            </code>
                          </pre>
                        </div>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
                {typeof message.processing_seconds === "number" ? (
                  <div className="message-meta">Processed in {message.processing_seconds}s</div>
                ) : null}
              </div>
            ) : (
              <p>{message.content}</p>
            )}
          </div>
        ))
      )}
    </div>
  );
}
