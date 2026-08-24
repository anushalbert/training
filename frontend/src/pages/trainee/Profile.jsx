import { useState } from "react";
import client from "../../api/client";
import { useAuth } from "../../context/AuthContext";

export default function Profile() {
  const { user, setUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [message, setMessage] = useState("");

  async function handleSave(e) {
    e.preventDefault();
    const { data } = await client.patch("/users/me", { full_name: fullName, bio });
    setUser(data);
    setMessage("Profile updated.");
  }

  return (
    <div className="container">
      <h1>My Profile</h1>
      <div className="card" style={{ maxWidth: 480 }}>
        <form onSubmit={handleSave}>
          <label>Full name</label>
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          <label>Bio</label>
          <textarea rows={4} value={bio} onChange={(e) => setBio(e.target.value)} />
          {message && <p className="success-text">{message}</p>}
          <button type="submit">Save</button>
        </form>
      </div>
    </div>
  );
}
