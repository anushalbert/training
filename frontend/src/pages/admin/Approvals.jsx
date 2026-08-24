import { useEffect, useState } from "react";
import { listPendingUsers, approveUser } from "../../api/courses";

export default function Approvals() {
  const [pending, setPending] = useState([]);
  const [error, setError] = useState("");

  function load() {
    listPendingUsers()
      .then(setPending)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load pending users"));
  }

  useEffect(load, []);

  async function handleApprove(id) {
    try {
      await approveUser(id);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Approval failed");
    }
  }

  return (
    <div className="card">
      <h3>Pending Approvals</h3>
      {error && <p className="error-text">{error}</p>}
      {pending.length === 0 ? (
        <p className="muted">No pending approvals.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {pending.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>
                  <button onClick={() => handleApprove(u.id)}>Approve</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
