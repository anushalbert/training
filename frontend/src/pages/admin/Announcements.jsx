import { useEffect, useState } from "react";
import { listAnnouncements, createAnnouncement, deleteAnnouncement } from "../../api/courses";

export default function Announcements() {
  const [items, setItems] = useState([]);
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function load() {
    listAnnouncements().then(setItems).catch(() => {});
  }

  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      await createAnnouncement({ title, message });
      setTitle("");
      setMessage("");
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to post announcement");
    }
  }

  async function handleDelete(id) {
    await deleteAnnouncement(id);
    load();
  }

  return (
    <div className="grid grid-2">
      <div className="card">
        <h3>New Announcement</h3>
        <form onSubmit={handleCreate}>
          <label>Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          <label>Message</label>
          <textarea rows={4} value={message} onChange={(e) => setMessage(e.target.value)} required />
          {error && <p className="error-text">{error}</p>}
          <button type="submit">Post</button>
        </form>
      </div>
      <div className="card">
        <h3>All Announcements</h3>
        {items.map((a) => (
          <div key={a.id} style={{ marginBottom: 12, borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
            <strong>{a.title}</strong>
            <p className="muted">{a.message}</p>
            <button className="danger" onClick={() => handleDelete(a.id)}>
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
