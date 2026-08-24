import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { getCourse } from "../../api/courses";
import { getCourseWeeks, getCourseQA } from "../../api/content";
import { getCourseProgress, completeLesson, listNotes, createNote, deleteNote } from "../../api/progress";
import { useAuth } from "../../context/AuthContext";
import QuizModal from "../../components/QuizModal";
import TutorPanel from "../../components/TutorPanel";

function ContentBlock({ block }) {
  if (block.block_type === "formula") {
    return (
      <div className="block-formula">
        {block.label && <div className="formula-label">{block.label}</div>}
        <p className="formula-expression">{block.expression}</p>
        {block.explanation && <p className="formula-explanation">{block.explanation}</p>}
      </div>
    );
  }

  if (block.block_type === "example") {
    return (
      <div className="block-example">
        <div className="example-label">Example</div>
        <p style={{ margin: 0 }}>{block.body}</p>
      </div>
    );
  }

  if (block.block_type === "diagram_suggestion") {
    return (
      <div className="block-diagram" role="img" aria-label={block.body}>
        [Diagram: {block.body}]
      </div>
    );
  }

  return (
    <div className="block-text">
      {block.heading && <h4>{block.heading}</h4>}
      <p>{block.body}</p>
    </div>
  );
}

function findMatchingAnchors(block, anchors, matchedIds) {
  const matches = [];
  const text = `${block.heading || ""} ${block.body || ""} ${block.expression || ""}`.toLowerCase();
  for (const anchor of anchors) {
    if (matchedIds.has(anchor.id)) continue;
    if (anchor.anchor_text && text.includes(anchor.anchor_text.toLowerCase().slice(0, 40))) {
      matches.push(anchor);
      matchedIds.add(anchor.id);
    }
  }
  return matches;
}

export default function CourseContent() {
  const { courseId } = useParams();
  const { user } = useAuth();
  const previewMode = user?.role !== "trainee";

  const [course, setCourse] = useState(null);
  const [weeks, setWeeks] = useState([]);
  const [qa, setQa] = useState([]);
  const [progress, setProgress] = useState(null);
  const [selectedLessonId, setSelectedLessonId] = useState(null);
  const [expandedWeeks, setExpandedWeeks] = useState(new Set());
  const [error, setError] = useState("");
  const [quizWeek, setQuizWeek] = useState(null);
  const [notes, setNotes] = useState([]);
  const [noteDraft, setNoteDraft] = useState("");
  const [selectedText, setSelectedText] = useState("");
  const [tutorOpen, setTutorOpen] = useState(false);
  const mainRef = useRef(null);
  const autoCompletedRef = useRef(new Set());

  function loadCore() {
    Promise.all([getCourse(courseId), getCourseWeeks(courseId), getCourseQA(courseId)])
      .then(([c, w, q]) => {
        setCourse(c);
        setWeeks(w);
        setQa(q);
        if (w.length > 0) {
          setExpandedWeeks(new Set([w[0].week_number]));
          if (w[0].lessons.length > 0) setSelectedLessonId(w[0].lessons[0].id);
        }
      })
      .catch((err) => setError(err.response?.data?.detail || "Failed to load course content"));
  }

  function loadProgress() {
    if (previewMode) return;
    getCourseProgress(courseId)
      .then(setProgress)
      .catch(() => {});
  }

  useEffect(loadCore, [courseId]);
  useEffect(loadProgress, [courseId]);

  useEffect(() => {
    if (!selectedLessonId || previewMode) return;
    listNotes(selectedLessonId)
      .then(setNotes)
      .catch(() => setNotes([]));
  }, [selectedLessonId, previewMode]);

  const flatLessons = useMemo(() => {
    const out = [];
    for (const w of weeks) {
      for (const l of w.lessons) out.push({ ...l, week_number: w.week_number });
    }
    return out;
  }, [weeks]);

  const currentLesson = flatLessons.find((l) => l.id === selectedLessonId);
  const currentWeek = weeks.find((w) => w.week_number === currentLesson?.week_number);

  const weekProgress = (weekNumber) => progress?.weeks.find((w) => w.week_number === weekNumber);
  const isCompleted = (lessonId) => progress?.completed_lesson_ids.includes(lessonId);
  const isWeekUnlocked = (weekNumber) => previewMode || weekProgress(weekNumber)?.unlocked !== false;

  function toggleWeek(weekNumber) {
    if (!isWeekUnlocked(weekNumber)) return;
    setExpandedWeeks((prev) => {
      const next = new Set(prev);
      if (next.has(weekNumber)) next.delete(weekNumber);
      else next.add(weekNumber);
      return next;
    });
  }

  function selectLesson(lessonId, weekNumber) {
    if (!isWeekUnlocked(weekNumber)) return;
    setSelectedLessonId(lessonId);
    setNoteDraft("");
    setSelectedText("");
  }

  async function markComplete(lessonId) {
    if (previewMode) return;
    try {
      await completeLesson(lessonId);
      const updated = await getCourseProgress(courseId);
      setProgress(updated);

      const wp = updated.weeks.find((w) => w.week_number === currentLesson.week_number);
      if (wp && wp.lessons_done && wp.quiz_required && !wp.quiz_passed) {
        setQuizWeek(currentLesson.week_number);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save progress");
    }
  }

  function handleScroll() {
    if (previewMode || !currentLesson) return;
    const el = mainRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    if (nearBottom && !autoCompletedRef.current.has(currentLesson.id) && !isCompleted(currentLesson.id)) {
      autoCompletedRef.current.add(currentLesson.id);
      markComplete(currentLesson.id);
    }
  }

  function handleTextSelect() {
    const sel = window.getSelection()?.toString() || "";
    setSelectedText(sel.trim());
  }

  async function handleSaveNote() {
    if (!noteDraft.trim() || !currentLesson) return;
    try {
      const note = await createNote(currentLesson.id, { anchor_text: selectedText || null, note_text: noteDraft });
      setNotes((prev) => [note, ...prev]);
      setNoteDraft("");
      setSelectedText("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save note");
    }
  }

  async function handleDeleteNote(noteId) {
    await deleteNote(noteId);
    setNotes((prev) => prev.filter((n) => n.id !== noteId));
  }

  function handleQuizPassed() {
    setQuizWeek(null);
    loadProgress();
  }

  if (error && !course) return <div className="container error-text">{error}</div>;
  if (!course) return <div className="container muted">Loading...</div>;

  const matchedAnchorIds = new Set();

  return (
    <div className="player-shell">
      <div className="player-sidebar">
        <div className="progress-header">
          <div className="content">
            <h2>{course.title}</h2>
            {previewMode ? (
              <p className="muted" style={{ margin: 0 }}>
                Preview mode — progress tracking is trainee-only.
              </p>
            ) : (
              <>
                <span className="progress-pct">
                  {progress ? `${progress.completed_lessons}/${progress.total_lessons} lessons — ${progress.percent}%` : "—"}
                </span>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill" style={{ width: `${progress?.percent || 0}%` }} />
                </div>
              </>
            )}
          </div>
        </div>

        {weeks.map((w) => {
          const unlocked = isWeekUnlocked(w.week_number);
          const expanded = expandedWeeks.has(w.week_number);
          return (
            <div className="week-block" key={w.id}>
              <div className={`week-header ${unlocked ? "" : "locked"}`} onClick={() => toggleWeek(w.week_number)}>
                <span className="week-num">W{w.week_number}</span>
                <span className="week-title">{w.title}</span>
                {!unlocked && <span className="lock-icon">🔒</span>}
              </div>
              {expanded &&
                unlocked &&
                w.lessons.map((l) => (
                  <div
                    key={l.id}
                    className={`lesson-row ${selectedLessonId === l.id ? "active" : ""}`}
                    onClick={() => selectLesson(l.id, w.week_number)}
                  >
                    <span className={`check ${!previewMode && isCompleted(l.id) ? "" : "incomplete"}`}>
                      {!previewMode && isCompleted(l.id) ? "✓" : "○"}
                    </span>
                    {l.title}
                  </div>
                ))}
            </div>
          );
        })}
      </div>

      <div className="player-main" ref={mainRef} onScroll={handleScroll} onMouseUp={handleTextSelect}>
        {error && <p className="error-text">{error}</p>}
        {!currentLesson ? (
          <p className="muted">Select a lesson to begin.</p>
        ) : (
          <>
            <h1>{currentLesson.title}</h1>
            {currentLesson.content_blocks.map((b) => {
              const anchors = findMatchingAnchors(b, currentLesson.note_anchors, matchedAnchorIds);
              return (
                <div key={b.id}>
                  <ContentBlock block={b} />
                  {anchors.map((a) => (
                    <div className="note-anchor-hint" key={a.id}>
                      Reflect: {a.suggested_note_prompt}
                    </div>
                  ))}
                </div>
              );
            })}
            {currentLesson.note_anchors
              .filter((a) => !matchedAnchorIds.has(a.id))
              .map((a) => (
                <div className="note-anchor-hint" key={a.id}>
                  Reflect: {a.suggested_note_prompt}
                </div>
              ))}

            {!previewMode && (
              <>
                <div className="card" style={{ marginTop: 24 }}>
                  <strong>Notes</strong>
                  <p className="muted" style={{ marginTop: 4 }}>
                    Highlight any text above, then attach a note to it — or just jot a general note.
                  </p>
                  {selectedText && (
                    <p className="muted">
                      Selected: <em>"{selectedText.slice(0, 80)}{selectedText.length > 80 ? "…" : ""}"</em>
                    </p>
                  )}
                  <textarea rows={2} value={noteDraft} onChange={(e) => setNoteDraft(e.target.value)} placeholder="Your note" />
                  <button className="secondary" onClick={handleSaveNote} disabled={!noteDraft.trim()}>
                    Save note
                  </button>
                  {notes.map((n) => (
                    <div key={n.id} style={{ marginTop: 10, borderTop: "1px solid var(--border)", paddingTop: 8 }}>
                      {n.anchor_text && <p className="muted" style={{ margin: 0 }}>On: "{n.anchor_text.slice(0, 60)}"</p>}
                      <p style={{ margin: "2px 0" }}>{n.note_text}</p>
                      <button className="secondary" onClick={() => handleDeleteNote(n.id)}>
                        Delete
                      </button>
                    </div>
                  ))}
                </div>

                <div className="lesson-nav">
                  <span />
                  <button onClick={() => markComplete(currentLesson.id)} disabled={isCompleted(currentLesson.id)}>
                    {isCompleted(currentLesson.id) ? "Completed" : "Mark as complete"}
                  </button>
                </div>
              </>
            )}
          </>
        )}

        {qa.length > 0 && (
          <div className="card" style={{ marginTop: 24 }}>
            <h2>AI Q&amp;A: Concept Clarification</h2>
            {qa.map((item) => (
              <details key={item.id} style={{ marginBottom: 8 }}>
                <summary style={{ cursor: "pointer", fontWeight: 500 }}>{item.question}</summary>
                <p className="muted">{item.answer}</p>
              </details>
            ))}
          </div>
        )}
      </div>

      {quizWeek !== null && (
        <QuizModal
          courseId={courseId}
          weekNumber={quizWeek}
          onPassed={handleQuizPassed}
          onExit={() => setQuizWeek(null)}
        />
      )}

      {!previewMode && currentLesson && !tutorOpen && (
        <button className="tutor-toggle" onClick={() => setTutorOpen(true)}>
          Ask the tutor
        </button>
      )}
      {!previewMode && currentLesson && tutorOpen && (
        <TutorPanel lessonId={currentLesson.id} onClose={() => setTutorOpen(false)} />
      )}
    </div>
  );
}
