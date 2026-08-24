import { useEffect, useRef, useState } from "react";
import { getTutorMessages, sendTutorMessage } from "../api/tutor";

export default function TutorPanel({ lessonId, onClose }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    getTutorMessages(lessonId)
      .then((data) => setMessages(data.messages))
      .catch(() => setMessages([]));
  }, [lessonId]);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    if (!draft.trim()) return;
    setSending(true);
    setError("");
    const optimistic = [...messages, { role: "user", content: draft }];
    setMessages(optimistic);
    const sent = draft;
    setDraft("");
    try {
      const data = await sendTutorMessage(lessonId, sent);
      setMessages(data.messages);
    } catch (err) {
      setError(err.response?.data?.detail || "The tutor is unavailable right now.");
      setMessages(messages);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="tutor-panel">
      <div className="tutor-panel-header">
        <h3>Ask the tutor</h3>
        <button className="secondary" onClick={onClose}>
          Close
        </button>
      </div>
      <div className="tutor-messages" ref={listRef}>
        {messages.length === 0 && (
          <p className="muted">
            Ask a question about this lesson. The tutor answers from this lesson's content only — it won't give
            away quiz answers.
          </p>
        )}
        {messages.map((m, i) => (
          <div className={`tutor-message ${m.role}`} key={i}>
            <span className="role">{m.role === "user" ? "You" : "Tutor"}</span>
            {m.content}
          </div>
        ))}
        {error && <p className="error-text">{error}</p>}
      </div>
      <form className="tutor-panel-footer" onSubmit={handleSend}>
        <textarea
          rows={2}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about this lesson..."
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend(e);
            }
          }}
        />
        <button type="submit" disabled={sending || !draft.trim()}>
          {sending ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
