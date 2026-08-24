import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getCourse } from "../../api/courses";
import { getCourseWeeks, getCourseQA } from "../../api/content";

function ContentBlock({ block }) {
  if (block.block_type === "formula") {
    return (
      <div className="card" style={{ background: "var(--bg)" }}>
        {block.label && <strong>{block.label}</strong>}
        <pre
          style={{
            whiteSpace: "pre-wrap",
            fontFamily: "ui-monospace, Consolas, monospace",
            background: "#fff",
            border: "1px solid var(--border)",
            borderRadius: 6,
            padding: 10,
            margin: "8px 0",
          }}
        >
          {block.expression}
        </pre>
        {block.explanation && <p className="muted">{block.explanation}</p>}
      </div>
    );
  }

  if (block.block_type === "example") {
    return (
      <div className="card" style={{ background: "var(--bg)", borderLeft: "3px solid var(--primary)" }}>
        <p style={{ margin: 0 }}>
          <strong>Example: </strong>
          {block.body}
        </p>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: 12 }}>
      {block.heading && <h4 style={{ marginBottom: 4 }}>{block.heading}</h4>}
      <p style={{ marginTop: 0 }}>{block.body}</p>
    </div>
  );
}

function Lesson({ lesson }) {
  return (
    <div className="card">
      <h3>{lesson.title}</h3>
      {lesson.content_blocks.map((b) => (
        <ContentBlock key={b.id} block={b} />
      ))}
      {lesson.note_anchors.length > 0 && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px dashed var(--border)" }}>
          {lesson.note_anchors.map((na) => (
            <div key={na.id} style={{ marginBottom: 8 }}>
              <span className="muted">Reflect: </span>
              <em>{na.suggested_note_prompt}</em>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Week({ week, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="card">
      <div
        style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}
        onClick={() => setOpen((o) => !o)}
      >
        <h2 style={{ margin: 0 }}>
          Week {week.week_number}: {week.title}
        </h2>
        <span className="muted">{open ? "▲" : "▼"}</span>
      </div>
      {week.overview && <p className="muted">{week.overview}</p>}
      {week.estimated_minutes && <p className="muted">Est. {week.estimated_minutes} minutes</p>}

      {open && (
        <>
          {week.lessons.map((lesson) => (
            <Lesson key={lesson.id} lesson={lesson} />
          ))}

          {week.completion_criteria.length > 0 && (
            <div className="card" style={{ background: "var(--bg)" }}>
              <strong>By the end of this week, you should be able to:</strong>
              <ul>
                {week.completion_criteria.map((c) => (
                  <li key={c.id}>{c.criterion_text}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function QAAccordion({ items }) {
  const [openId, setOpenId] = useState(null);
  if (items.length === 0) return null;

  return (
    <div className="card">
      <h2>AI Q&amp;A: Concept Clarification</h2>
      {items.map((item) => (
        <div key={item.id} style={{ borderBottom: "1px solid var(--border)", padding: "10px 0" }}>
          <div style={{ cursor: "pointer" }} onClick={() => setOpenId(openId === item.id ? null : item.id)}>
            <strong>{item.question}</strong>{" "}
            {item.difficulty && <span className="badge">{item.difficulty}</span>}
          </div>
          {openId === item.id && <p className="muted" style={{ marginTop: 8 }}>{item.answer}</p>}
        </div>
      ))}
    </div>
  );
}

export default function CourseContent() {
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [weeks, setWeeks] = useState([]);
  const [qa, setQa] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getCourse(courseId), getCourseWeeks(courseId), getCourseQA(courseId)])
      .then(([c, w, q]) => {
        setCourse(c);
        setWeeks(w);
        setQa(q);
      })
      .catch((err) => setError(err.response?.data?.detail || "Failed to load course content"));
  }, [courseId]);

  if (error) return <div className="container error-text">{error}</div>;
  if (!course) return <div className="container muted">Loading...</div>;

  const meta = course.meta || {};

  return (
    <div className="container">
      <h1>{course.title}</h1>
      <div className="card">
        {meta.tier && <span className="badge" style={{ marginRight: 8 }}>{meta.tier}</span>}
        {meta.difficulty && <span className="badge">{meta.difficulty}</span>}
        {meta.author && <p className="muted">By {meta.author}</p>}
        {meta.estimated_hours && <p className="muted">Estimated: {meta.estimated_hours} hours</p>}
        {meta.prerequisites?.length > 0 && (
          <p className="muted">Prerequisites: {meta.prerequisites.join(", ")}</p>
        )}
        {meta.source_url && (
          <p className="muted">
            Source:{" "}
            <a href={meta.source_url} target="_blank" rel="noreferrer">
              {meta.source_pdf || meta.source_url}
            </a>
          </p>
        )}
      </div>

      {weeks.length === 0 ? (
        <p className="muted">No structured lesson content has been added to this course yet.</p>
      ) : (
        weeks.map((w, i) => <Week key={w.id} week={w} defaultOpen={i === 0} />)
      )}

      <QAAccordion items={qa} />
    </div>
  );
}
