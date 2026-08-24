import { useEffect, useState } from "react";
import { listCourses, suggestTrainers, assignTrainer } from "../../api/courses";

export default function CourseAssignment() {
  const [courses, setCourses] = useState([]);
  const [selected, setSelected] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    listCourses().then(setCourses).catch(() => {});
  }, []);

  async function handleSuggest(course) {
    setSelected(course.id);
    setError("");
    try {
      const data = await suggestTrainers(course.id);
      setSuggestions(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to fetch suggestions");
      setSuggestions([]);
    }
  }

  async function handleAssign(courseId, trainerId) {
    await assignTrainer(courseId, trainerId);
    const data = await listCourses();
    setCourses(data);
  }

  return (
    <div className="grid grid-2">
      <div className="card">
        <h3>Courses</h3>
        {courses.map((c) => (
          <div key={c.id} style={{ marginBottom: 10, borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
            <strong>{c.title}</strong>{" "}
            <span className="muted">
              ({c.status}, trainer: {c.trainer_id ? c.trainer_id.slice(0, 8) : "unassigned"})
            </span>
            <br />
            <button className="secondary" onClick={() => handleSuggest(c)}>
              Suggest trainers (competency match)
            </button>
          </div>
        ))}
      </div>
      <div className="card">
        <h3>Trainer Suggestions</h3>
        {error && <p className="error-text">{error}</p>}
        {!selected && <p className="muted">Select a course to see competency-matched trainers.</p>}
        {selected && suggestions.length === 0 && !error && (
          <p className="muted">No matching trainers found (course may have no required competencies set).</p>
        )}
        {suggestions.map((s) => (
          <div key={s.trainer_id} style={{ marginBottom: 10 }}>
            <strong>{s.full_name}</strong> — score {(s.match_score * 100).toFixed(0)}%
            <div className="muted">Matched: {s.matched_competencies.join(", ")}</div>
            <button onClick={() => handleAssign(selected, s.trainer_id)}>Assign</button>
          </div>
        ))}
      </div>
    </div>
  );
}
