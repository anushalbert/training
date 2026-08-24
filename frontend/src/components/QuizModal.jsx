import { useEffect, useState } from "react";
import { getWeekQuiz, submitWeekQuiz } from "../api/progress";

export default function QuizModal({ courseId, weekNumber, onPassed, onExit }) {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [confirmingExit, setConfirmingExit] = useState(false);

  function load() {
    setError("");
    setResult(null);
    setAnswers({});
    getWeekQuiz(courseId, weekNumber)
      .then(setQuiz)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load quiz"));
  }

  useEffect(load, [courseId, weekNumber]);

  function setAnswer(questionId, value) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const data = await submitWeekQuiz(courseId, weekNumber, answers);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="quiz-overlay">
      <div className="quiz-modal">
        {!result && (
          <>
            <div className="quiz-meta">Week {weekNumber} — gating quiz</div>
            <h2>Section check: you must pass to continue</h2>
            {error && <p className="error-text">{error}</p>}
            {!quiz ? (
              <p className="muted">Loading quiz...</p>
            ) : (
              <form onSubmit={handleSubmit}>
                {quiz.questions.map((q, i) => (
                  <div className="quiz-question" key={q.id}>
                    <div className="q-text">
                      {i + 1}. {q.question_text}
                    </div>
                    {(q.question_type === "mcq" || q.question_type === "true_false") &&
                      ["a", "b", "c", "d"]
                        .filter((opt) => q[`option_${opt}`] != null)
                        .map((opt) => (
                          <label className="quiz-option-row" key={opt}>
                            <input
                              type="radio"
                              name={q.id}
                              value={opt.toUpperCase()}
                              checked={answers[q.id] === opt.toUpperCase()}
                              onChange={() => setAnswer(q.id, opt.toUpperCase())}
                            />{" "}
                            {q[`option_${opt}`]}
                          </label>
                        ))}
                    {q.question_type === "fill_in_blank" && (
                      <input
                        type="text"
                        placeholder="Your answer"
                        value={answers[q.id] || ""}
                        onChange={(e) => setAnswer(q.id, e.target.value)}
                      />
                    )}
                    {q.question_type === "short_answer" && (
                      <textarea
                        rows={3}
                        placeholder="Your answer (reviewed, not auto-graded)"
                        value={answers[q.id] || ""}
                        onChange={(e) => setAnswer(q.id, e.target.value)}
                      />
                    )}
                  </div>
                ))}

                <div className="quiz-footer">
                  {!confirmingExit ? (
                    <button type="button" className="secondary" onClick={() => setConfirmingExit(true)}>
                      Exit without finishing
                    </button>
                  ) : (
                    <div>
                      <span className="muted" style={{ marginRight: 8 }}>
                        This attempt won't be saved.
                      </span>
                      <button type="button" className="secondary" onClick={() => setConfirmingExit(false)}>
                        Cancel
                      </button>{" "}
                      <button type="button" className="danger" onClick={onExit}>
                        Yes, exit
                      </button>
                    </div>
                  )}
                  <button type="submit" disabled={submitting}>
                    {submitting ? "Submitting..." : "Submit quiz"}
                  </button>
                </div>
              </form>
            )}
          </>
        )}

        {result && (
          <div>
            <div className="quiz-meta">Week {weekNumber} — result</div>
            <h2>{result.passed ? "Passed" : "Not yet"}</h2>
            <p>
              Score: <strong>{result.score}%</strong> ({result.correct_count}/{result.total_auto_gradable}{" "}
              auto-graded questions correct)
            </p>
            {result.short_answer_flagged.length > 0 && (
              <p className="muted">
                {result.short_answer_flagged.length} short-answer response(s) recorded for review — not counted
                toward the pass threshold.
              </p>
            )}
            {!result.passed && <p className="muted">You need at least 70% to unlock the next week. You can retry now.</p>}

            <div className="quiz-footer">
              <button className="secondary" onClick={onExit}>
                Back to lesson
              </button>
              {result.passed ? (
                <button onClick={onPassed}>Continue to next week</button>
              ) : (
                <button onClick={load}>Retry quiz</button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
