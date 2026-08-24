import { useEffect, useState } from "react";
import { getStats } from "../../api/courses";

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load stats"));
  }, []);

  if (error) return <p className="error-text">{error}</p>;
  if (!stats) return <p className="muted">Loading...</p>;

  const tiles = [
    { label: "Total Users", value: stats.total_users },
    { label: "Trainees", value: stats.total_trainees },
    { label: "Trainers", value: stats.total_trainers },
    { label: "Pending Approvals", value: stats.pending_approvals },
    { label: "Total Courses", value: stats.total_courses },
    { label: "Published Courses", value: stats.published_courses },
    { label: "Total Enrollments", value: stats.total_enrollments },
    { label: "Avg. Assessment Score", value: stats.average_assessment_score ?? "N/A" },
  ];

  return (
    <div className="grid grid-4">
      {tiles.map((t) => (
        <div className="card stat-tile" key={t.label}>
          <div className="value">{t.value}</div>
          <div className="label">{t.label}</div>
        </div>
      ))}
    </div>
  );
}
