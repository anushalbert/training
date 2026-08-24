import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { createAssessment, listAssessmentsForCourse, listSubmissions } from "../../api/assessments";

const emptyQuestion = () => ({
  question_type: "mcq",
  question_text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  correct_answer: "A",
  competency_tag: "",
});

export default function CreateQuestionnaire() {
  const { courseId } = useParams();
  const [title, setTitle] = useState("");
  const [questions, setQuestions] = useState([emptyQuestion()]);
  const [assessments, setAssessments] = useState([]);
  const [submissionsByAssessment, setSubmissionsByAssessment] = useState({});
  const [error, setError] = useState("");

  function load() {
    listAssessmentsForCourse(courseId).then(setAssessments).catch(() => {});
  }

  useEffect(load, [courseId]);

  function updateQuestion(index, field, value) {
    setQuestions((qs) => qs.map((q, i) => (i === index ? { ...q, [field]: value } : q)));
  }

  function addQuestion() {
    setQuestions((qs) => [...qs, emptyQuestion()]);
  }

  function removeQuestion(index) {
    setQuestions((qs) => qs.filter((_, i) => i !== index));
  }

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      const cleaned = questions.map((q) =>
        q.question_type === "mcq" || q.question_type === "true_false"
          ? q
          : { ...q, option_a: null, option_b: null, option_c: null, option_d: null }
      );
      await createAssessment({ course_id: courseId, title, questions: cleaned });
      setTitle("");
      setQuestions([emptyQuestion()]);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create questionnaire");
    }
  }

  async function handleViewSubmissions(assessmentId) {
    const data = await listSubmissions(assessmentId);
    setSubmissionsByAssessment((prev) => ({ ...prev, [assessmentId]: data }));
  }

  return (
    <div className="container">
      <h1>Create Questionnaire</h1>
      <div className="card">
        <form onSubmit={handleCreate}>
          <label>Assessment title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />

          {questions.map((q, i) => (
            <div key={i} className="card" style={{ background: "var(--bg)" }}>
              <label>Question {i + 1}</label>
              <textarea
                value={q.question_text}
                onChange={(e) => updateQuestion(i, "question_text", e.target.value)}
                required
              />
              <label>Question type</label>
              <select
                value={q.question_type}
                onChange={(e) => {
                  const type = e.target.value;
                  updateQuestion(i, "question_type", type);
                  updateQuestion(i, "correct_answer", type === "mcq" || type === "true_false" ? "A" : "");
                }}
              >
                <option value="mcq">Multiple choice (4 options)</option>
                <option value="true_false">True / False</option>
                <option value="fill_in_blank">Fill in the blank</option>
                <option value="short_answer">Short answer</option>
              </select>

              {q.question_type === "mcq" &&
                ["a", "b", "c", "d"].map((opt) => (
                  <input
                    key={opt}
                    placeholder={`Option ${opt.toUpperCase()}`}
                    value={q[`option_${opt}`]}
                    onChange={(e) => updateQuestion(i, `option_${opt}`, e.target.value)}
                    required
                  />
                ))}

              {q.question_type === "true_false" &&
                ["a", "b"].map((opt) => (
                  <input
                    key={opt}
                    placeholder={`Option ${opt.toUpperCase()} (e.g. True / False)`}
                    value={q[`option_${opt}`]}
                    onChange={(e) => updateQuestion(i, `option_${opt}`, e.target.value)}
                    required
                  />
                ))}

              {(q.question_type === "mcq" || q.question_type === "true_false") && (
                <>
                  <label>Correct option</label>
                  <select
                    value={q.correct_answer}
                    onChange={(e) => updateQuestion(i, "correct_answer", e.target.value)}
                  >
                    {(q.question_type === "mcq" ? ["A", "B", "C", "D"] : ["A", "B"]).map((letter) => (
                      <option key={letter} value={letter}>
                        {letter}
                      </option>
                    ))}
                  </select>
                </>
              )}

              {(q.question_type === "fill_in_blank" || q.question_type === "short_answer") && (
                <>
                  <label>Expected answer</label>
                  <input
                    value={q.correct_answer}
                    onChange={(e) => updateQuestion(i, "correct_answer", e.target.value)}
                    placeholder="Graded via a case-insensitive text match"
                    required
                  />
                </>
              )}

              <label>Competency tag (optional)</label>
              <input
                value={q.competency_tag}
                onChange={(e) => updateQuestion(i, "competency_tag", e.target.value)}
              />
              {questions.length > 1 && (
                <button type="button" className="danger" onClick={() => removeQuestion(i)}>
                  Remove question
                </button>
              )}
            </div>
          ))}

          <button type="button" className="secondary" onClick={addQuestion}>
            + Add question
          </button>
          {error && <p className="error-text">{error}</p>}
          <button type="submit">Save questionnaire</button>
        </form>
      </div>

      <h2>Existing Questionnaires</h2>
      {assessments.map((a) => (
        <div className="card" key={a.id}>
          <strong>{a.title}</strong>
          <div>
            <button className="secondary" onClick={() => handleViewSubmissions(a.id)}>
              View submissions
            </button>
          </div>
          {submissionsByAssessment[a.id] && (
            <table style={{ marginTop: 10 }}>
              <thead>
                <tr>
                  <th>Trainee</th>
                  <th>Score</th>
                  <th>Total Qs</th>
                </tr>
              </thead>
              <tbody>
                {submissionsByAssessment[a.id].map((s) => (
                  <tr key={s.id}>
                    <td>{s.trainee_id.slice(0, 8)}</td>
                    <td>{s.score}%</td>
                    <td>{s.total_questions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  );
}
