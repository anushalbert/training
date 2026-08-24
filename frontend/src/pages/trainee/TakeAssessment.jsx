import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getAssessment, submitAssessment } from "../../api/assessments";

export default function TakeAssessment() {
  const { assessmentId } = useParams();
  const [assessment, setAssessment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAssessment(assessmentId).then(setAssessment).catch((err) => setError(err.response?.data?.detail || "Failed to load assessment"));
  }, [assessmentId]);

  function selectAnswer(questionId, option) {
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await submitAssessment(assessmentId, answers);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed");
    }
  }

  if (error && !assessment) return <div className="container error-text">{error}</div>;
  if (!assessment) return <div className="container muted">Loading...</div>;

  if (result) {
    return (
      <div className="container">
        <div className="card">
          <h2>Result</h2>
          <p>
            Score: <strong>{result.score}%</strong> ({result.total_questions} questions)
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>{assessment.title}</h1>
      <form onSubmit={handleSubmit}>
        {assessment.questions.map((q, i) => (
          <div className="card" key={q.id}>
            <p>
              <strong>
                {i + 1}. {q.question_text}
              </strong>
            </p>
            {["a", "b", "c", "d"].map((opt) => (
              <label key={opt} style={{ display: "block", fontWeight: 400 }}>
                <input
                  type="radio"
                  name={q.id}
                  value={opt.toUpperCase()}
                  checked={answers[q.id] === opt.toUpperCase()}
                  onChange={() => selectAnswer(q.id, opt.toUpperCase())}
                />{" "}
                {q[`option_${opt}`]}
              </label>
            ))}
          </div>
        ))}
        {error && <p className="error-text">{error}</p>}
        <button type="submit">Submit assessment</button>
      </form>
    </div>
  );
}
