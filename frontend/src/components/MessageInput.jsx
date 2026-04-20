import { useState } from "react";

export default function MessageInput({ disabled, onSend }) {
  const [message, setMessage] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || disabled) return;
    await onSend(trimmed);
    setMessage("");
  };

  return (
    <form className="message-form" onSubmit={submit}>
      <input
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Type your message"
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !message.trim()}>
        Send
      </button>
    </form>
  );
}
