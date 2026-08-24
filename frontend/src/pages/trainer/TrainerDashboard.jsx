import { useEffect, useState } from "react";
import { listCourses, createCourse, myCompetencies, setMyCompetencies } from "../../api/courses";
import { Link } from "react-router-dom";

export default function TrainerDashboard() {
  const [courses, setCourses] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  const [competencies, setCompetencies] = useState([]);
  const [newSkill, setNewSkill] = useState("");
  const [newLevel, setNewLevel] = useState(3);

  function loadCourses() {
    listCourses().then(setCourses).catch(() => {});
  }

  function loadCompetencies() {
    myCompetencies().then(setCompetencies).catch(() => {});
  }

  useEffect(() => {
    loadCourses();
    loadCompetencies();
  }, []);

  async function handleCreateCourse(e) {
    e.preventDefault();
    setError("");
    try {
      await createCourse({ title, description, required_competencies: [] });
      setTitle("");
      setDescription("");
      loadCourses();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create course");
    }
  }

  async function handleAddCompetency(e) {
    e.preventDefault();
    const updated = [...competencies.map((c) => ({ competency: c.competency, proficiency_level: c.proficiency_level })), { competency: newSkill, proficiency_level: Number(newLevel) }];
    const saved = await setMyCompetencies(updated);
    setCompetencies(saved);
    setNewSkill("");
  }

  return (
    <div className="container">
      <h1>Trainer Dashboard</h1>

      <div className="grid grid-2">
        <div className="card">
          <h3>Create a Course</h3>
          <form onSubmit={handleCreateCourse}>
            <label>Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
            <label>Description</label>
            <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
            {error && <p className="error-text">{error}</p>}
            <button type="submit">Create</button>
          </form>
        </div>

        <div className="card">
          <h3>My Competencies</h3>
          <p className="muted">Used to match you to courses via competency-based assignment.</p>
          {competencies.map((c) => (
            <div key={c.id} className="muted">
              {c.competency} — level {c.proficiency_level}/5
            </div>
          ))}
          <form onSubmit={handleAddCompetency} style={{ marginTop: 12 }}>
            <label>Skill</label>
            <input value={newSkill} onChange={(e) => setNewSkill(e.target.value)} required />
            <label>Proficiency (1-5)</label>
            <input type="number" min={1} max={5} value={newLevel} onChange={(e) => setNewLevel(e.target.value)} />
            <button type="submit">Add</button>
          </form>
        </div>
      </div>

      <h2>My Courses</h2>
      <div className="grid grid-2">
        {courses.map((c) => (
          <div className="card" key={c.id}>
            <h3>{c.title}</h3>
            <p className="muted">{c.description}</p>
            <p className="muted">Status: {c.status}</p>
            <div style={{ display: "flex", gap: 8 }}>
              <Link to={`/trainer/courses/${c.id}/materials`}>
                <button className="secondary">Materials</button>
              </Link>
              <Link to={`/trainer/courses/${c.id}/questionnaire`}>
                <button className="secondary">Questionnaires</button>
              </Link>
              <Link to={`/trainer/courses/${c.id}/import-content`}>
                <button className="secondary">Import Content</button>
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
