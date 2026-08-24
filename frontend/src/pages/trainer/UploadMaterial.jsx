import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { listMaterials, uploadMaterial, deleteMaterial } from "../../api/courses";

export default function UploadMaterial() {
  const { courseId } = useParams();
  const [materials, setMaterials] = useState([]);
  const [title, setTitle] = useState("");
  const [fileUrl, setFileUrl] = useState("");
  const [error, setError] = useState("");

  function load() {
    listMaterials(courseId).then(setMaterials).catch(() => {});
  }

  useEffect(load, [courseId]);

  async function handleUpload(e) {
    e.preventDefault();
    setError("");
    try {
      // In production: upload the file to Supabase Storage / S3 client-side first,
      // then register the returned public URL here.
      await uploadMaterial(courseId, { title, file_url: fileUrl });
      setTitle("");
      setFileUrl("");
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    }
  }

  async function handleDelete(id) {
    await deleteMaterial(courseId, id);
    load();
  }

  return (
    <div className="container">
      <h1>Course Materials</h1>
      <div className="grid grid-2">
        <div className="card">
          <h3>Add Material</h3>
          <form onSubmit={handleUpload}>
            <label>Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
            <label>File URL</label>
            <input
              value={fileUrl}
              onChange={(e) => setFileUrl(e.target.value)}
              placeholder="https://.../slides.pdf"
              required
            />
            {error && <p className="error-text">{error}</p>}
            <button type="submit">Add</button>
          </form>
        </div>
        <div className="card">
          <h3>Materials</h3>
          {materials.map((m) => (
            <div key={m.id} style={{ marginBottom: 8 }}>
              <a href={m.file_url} target="_blank" rel="noreferrer">
                {m.title}
              </a>{" "}
              <button className="danger" onClick={() => handleDelete(m.id)}>
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
