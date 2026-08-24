import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCourses, enrollInCourse, myEnrollments, listAnnouncements } from "../../api/courses";

export default function TraineeDashboard() {
  const [courses, setCourses] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [error, setError] = useState("");

  function load() {
    listCourses().then(setCourses).catch(() => {});
    myEnrollments().then(setEnrollments).catch(() => {});
    listAnnouncements().then(setAnnouncements).catch(() => {});
  }

  useEffect(load, []);

  const enrolledCourseIds = new Set(enrollments.map((e) => e.course_id));

  async function handleEnroll(courseId) {
    setError("");
    try {
      await enrollInCourse(courseId);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Enrollment failed");
    }
  }

  return (
    <div className="container">
      <h1>Trainee Dashboard</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <Link to="/trainee/profile">
          <button className="secondary">My Profile</button>
        </Link>
        <Link to="/trainee/enrollments">
          <button className="secondary">My Enrollments</button>
        </Link>
      </div>

      {announcements.length > 0 && (
        <div className="card">
          <h3>Announcements</h3>
          {announcements.map((a) => (
            <div key={a.id} style={{ marginBottom: 8 }}>
              <strong>{a.title}</strong>
              <p className="muted">{a.message}</p>
            </div>
          ))}
        </div>
      )}

      {error && <p className="error-text">{error}</p>}

      <h2>Available Courses</h2>
      <div className="grid grid-2">
        {courses.map((c) => (
          <div className="card" key={c.id}>
            <h3>{c.title}</h3>
            <p className="muted">{c.description}</p>
            {enrolledCourseIds.has(c.id) ? (
              <span className="success-text">Enrolled</span>
            ) : (
              <button onClick={() => handleEnroll(c.id)}>Enroll</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
