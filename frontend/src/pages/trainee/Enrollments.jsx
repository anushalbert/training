import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { myEnrollments, listCourses, listAssessmentsForCourse, submitFeedback } from "../../api/courses";

export default function Enrollments() {
  const [enrollments, setEnrollments] = useState([]);
  const [courses, setCourses] = useState({});
  const [assessmentsByCourse, setAssessmentsByCourse] = useState({});
  const [feedbackState, setFeedbackState] = useState({});

  useEffect(() => {
    myEnrollments().then(async (data) => {
      setEnrollments(data);
      const allCourses = await listCourses();
      const map = Object.fromEntries(allCourses.map((c) => [c.id, c]));
      setCourses(map);

      const assessmentsMap = {};
      for (const e of data) {
        assessmentsMap[e.course_id] = await listAssessmentsForCourse(e.course_id);
      }
      setAssessmentsByCourse(assessmentsMap);
    });
  }, []);

  async function handleFeedbackSubmit(courseId, rating, comments) {
    await submitFeedback({ course_id: courseId, rating: Number(rating), comments });
    setFeedbackState((prev) => ({ ...prev, [courseId]: "Submitted!" }));
  }

  return (
    <div className="container">
      <h1>My Enrollments</h1>
      <div className="grid grid-2">
        {enrollments.map((e) => {
          const course = courses[e.course_id];
          const assessments = assessmentsByCourse[e.course_id] || [];
          return (
            <div className="card" key={e.id}>
              <h3>{course?.title || "Course"}</h3>
              <p className="muted">Status: {e.status}</p>

              <div style={{ margin: "10px 0" }}>
                <strong>Assessments</strong>
                {assessments.length === 0 && <p className="muted">None yet.</p>}
                {assessments.map((a) => (
                  <div key={a.id}>
                    <Link to={`/trainee/assessments/${a.id}`}>{a.title}</Link>
                  </div>
                ))}
              </div>

              <FeedbackForm
                courseId={e.course_id}
                message={feedbackState[e.course_id]}
                onSubmit={handleFeedbackSubmit}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FeedbackForm({ courseId, message, onSubmit }) {
  const [rating, setRating] = useState(5);
  const [comments, setComments] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit(courseId, rating, comments);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>Feedback rating (1-5)</label>
      <input type="number" min={1} max={5} value={rating} onChange={(e) => setRating(e.target.value)} />
      <label>Comments</label>
      <textarea rows={2} value={comments} onChange={(e) => setComments(e.target.value)} />
      {message && <p className="success-text">{message}</p>}
      <button type="submit">Submit feedback</button>
    </form>
  );
}
