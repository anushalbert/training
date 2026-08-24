import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { importCourseContent } from "../../api/content";

export default function ImportContent() {
  const { courseId } = useParams();
  const [fileName, setFileName] = useState("");
  const [parsed, setParsed] = useState(null);
  const [createAssessment, setCreateAssessment] = useState(true);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setFileName(file.name);
    setError("");
    setResult(null);

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const json = JSON.parse(reader.result);
        setParsed(json);
      } catch {
        setError("That file isn't valid JSON.");
        setParsed(null);
      }
    };
    reader.readAsText(file);
  }

  async function handleImport() {
    if (!parsed) return;
    setSubmitting(true);
    setError("");
    try {
      const data = await importCourseContent(courseId, { ...parsed, create_assessment: createAssessment });
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Import failed — check the file matches the expected format.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container">
      <h1>Import Course Content</h1>
      <p className="muted">
        Upload a structured course-content JSON file (course_meta + weeks + lessons + ai_test_questions) — the
        format produced from a training PDF. This creates the full lesson viewer content for trainees and,
        optionally, an auto-graded assessment from the included test questions.
      </p>

      <div className="card">
        <label>Course content JSON file</label>
        <input type="file" accept=".json,application/json" onChange={handleFile} />

        {parsed && (
          <div className="card" style={{ background: "var(--bg)", marginTop: 12 }}>
            <strong>{fileName}</strong>
            <p className="muted">
              Subject: {parsed.course_meta?.subject || "—"} | Weeks: {parsed.weeks?.length ?? 0} | Test questions:{" "}
              {parsed.ai_test_questions?.length ?? 0} | Q&amp;A items: {parsed.ai_qa_concept_clarification?.length ?? 0}
            </p>
          </div>
        )}

        <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12 }}>
          <input
            type="checkbox"
            checked={createAssessment}
            onChange={(e) => setCreateAssessment(e.target.checked)}
            style={{ width: "auto" }}
          />
          Build an assessment from the included test questions
        </label>

        {error && <p className="error-text">{error}</p>}

        <button onClick={handleImport} disabled={!parsed || submitting} style={{ marginTop: 12 }}>
          {submitting ? "Importing..." : "Import content"}
        </button>
      </div>

      {result && (
        <div className="card success-text">
          <p>Imported successfully.</p>
          <ul>
            <li>{result.weeks_created} weeks</li>
            <li>{result.lessons_created} lessons</li>
            <li>{result.qa_items_created} Q&amp;A items</li>
            <li>{result.questions_created} assessment questions</li>
          </ul>
          {result.skipped_questions?.length > 0 && (
            <p className="muted">
              Skipped {result.skipped_questions.length} question(s) whose correct answer didn't match any option
              text exactly: {result.skipped_questions.join("; ")}
            </p>
          )}
          <Link to={`/trainer/courses/${courseId}/content-preview`}>
            <button className="secondary">View as trainee would see it</button>
          </Link>
        </div>
      )}
    </div>
  );
}
