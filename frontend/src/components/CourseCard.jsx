export default function CourseCard({ course, actions }) {
  return (
    <div className="card">
      <h3>{course.title}</h3>
      <p className="muted">{course.description || "No description provided."}</p>
      <p className="muted">
        Status: <strong>{course.status}</strong>
      </p>
      {actions && <div style={{ display: "flex", gap: 8, marginTop: 12 }}>{actions}</div>}
    </div>
  );
}
